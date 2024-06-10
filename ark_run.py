#!/usr/bin/env python

import importlib.util
import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(PROJECT_DIR, "api", "configs")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "empty.json")


def _check_help():
    if len(sys.argv) > 1 and sys.argv[1] in {"help", "--help", "-h"}:
        return True
    return False


def cli_entrypoint(model_name="auto"):
    cli_help = \
        """
        Convenience tool to launch flask server using gunicorn.

        In the simplest case, you can simply run:
        $ ark-run

        This will automatically detect the model in the current environment and launch the server.
        The model must be installed in the current environment; this can be done simply with:

        $ pip install 'ark[mirai]'

        or 

        $ pip install 'ark[sybil]'

        It is not recommended to install both models in the same environment, 
        as they have slightly different dependencies.


        If you'd like to specify a model, you can run:
        $ ark-run <model_name>

        where <model_name> is one of "empty", "mirai", or "sybil".

        $ ark-run empty

        will launch the server with an empty model, which is useful for testing the API.
        """

    if _check_help():
        print(cli_help)
        exit(0)

    if len(sys.argv) > 1:
        model_name = sys.argv[1]

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

    LOGLEVEL_KEY = "LOG_LEVEL"
    loglevel = os.environ.get(LOGLEVEL_KEY, "INFO")
    args = ["gunicorn",
            "--bind", "0.0.0.0:5000",
            "--timeout", "0",
            "--threads", "4",
            "--log-level", loglevel,
            "--access-logfile", "-",
            "main:create_app()"]

    proc = subprocess.run(args, stdout=None, stderr=None, text=True)


def cli_entrypoint_empty():
    cli_entrypoint("empty")


def cli_entrypoint_mirai():
    import onconet
    cli_entrypoint("mirai")


def cli_entrypoint_sybil():
    import sybil
    cli_entrypoint("sybil")
