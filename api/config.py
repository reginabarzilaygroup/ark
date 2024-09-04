import importlib
import importlib.util
import json
import os


import dotenv

from api import __version__ as api_version

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_DIR, "api", "configs")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "empty.json")

def configure_loggers():
    from api.logging_utils import configure_logger, LOGLEVEL_KEY
    log_level = os.environ.get(LOGLEVEL_KEY, "INFO").upper()
    logger_names = ["ark", "mirai", "sybil"]
    for name in logger_names:
        configure_logger(loglevel=log_level, logger_name=name)


def common_setup():
    ENV_FILE = os.getenv('ARK_ENV_FILE', None)
    if ENV_FILE:
        dotenv.load_dotenv(ENV_FILE)

    configure_loggers()

def set_config_by_name(model_name):
    config_path = os.getenv('ARK_CONFIG', None)

    if config_path is None:
        # If model name is specified, use that. Otherwise, detect automatically.
        if model_name == "auto":
            if importlib.util.find_spec("onconet"):
                model_name = "mirai"
            elif importlib.util.find_spec("sybil"):
                model_name = "sybil"
            else:
                print("No model found in the current environment. Using empty model.")
                model_name = "empty"

        config_path = os.path.join(CONFIG_DIR, f"{model_name}.json")
        assert os.path.exists(config_path), f"Config file not found at {config_path}"
        os.environ['ARK_CONFIG'] = config_path

    return config_path


def get_config(model_name="auto"):
    config_path = os.getenv('ARK_CONFIG', None)
    if config_path is None:
        config_path = set_config_by_name(model_name)

    if config_path is None:
        print(f"Warning: No config path provided to ARK. Using default config at {DEFAULT_CONFIG_PATH}.")
        print(f"To actually load a predictive model, set the ARK_CONFIG environment variable."
              f"For example:\nARK_CONFIG=api/configs/mirai.json python main.py\nWould load the Mirai model.")
        config_path = DEFAULT_CONFIG_PATH

    with open(config_path, 'r') as f:
        config = json.load(f)

    config['API_VERSION'] = api_version

    return config
