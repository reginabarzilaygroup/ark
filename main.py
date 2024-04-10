import json
import os
import sys

import dotenv

from api.app import build_app

DEFAULT_CONFIG_PATH = "api/configs/empty.json"

__doc__ = f"""
Ark: A simple tool for serving predictive models as web services.

Launch a web server to host the ARK API.
Running this script will start a Flask server that listens for incoming requests.
Parameters are set by environment variables. The following are supported:

ARK_CONFIG: Path to the configuration file that specifies the model to load. Default is {DEFAULT_CONFIG_PATH},
            which is an empty configuration. This is useful for testing the API without loading a model.
            Mirai config: api/configs/mirai.json
            Sybil config: api/configs/sybil.json
ARK_ENV_FILE: Path to a .env file to load environment variables from. Default is None.

ARK_FLASK_PORT: Port to run the Flask server on. Default is 5000.
ARK_FLASK_DEBUG: Whether to run the Flask server in debug mode. Default is false.

In a production environment, it is recommended to use a WSGI server like gunicorn to run the Flask app.

Examples:
# Run Flask server with Mirai config on port 5000
ARK_CONFIG=api/configs/mirai.json ARK_FLASK_PORT=5000 python main.py

# Run gunicorn server with Sybil config on port 5000, with 4 workers.
gunicorn -w 4 -b 0.0.0.0:5000 "main:create_app()" --env ARK_CONFIG="api/configs/sybil.json"

# The same thing written slightly differently.
ARK_CONFIG="api/configs/sybil.json" gunicorn -w 4 -b 0.0.0.0:5000 "main:create_app()"

For more information, see:
* README.md
* https://github.com/reginabarzilaygroup/ark/wiki

"""


def main():
    app = create_app()
    port = int(os.getenv('ARK_FLASK_PORT', 5000))
    debug = os.getenv('ARK_FLASK_DEBUG', "false").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug)


def create_app():
    config_path = os.getenv('ARK_CONFIG')
    if config_path is None:
        print(f"Warning: No config path provided to ARK. Using default config at {DEFAULT_CONFIG_PATH}.")
        print(f"To actually load a predictive model, set the ARK_CONFIG environment variable."
              f"For example:\nARK_CONFIG=api/configs/mirai.json python main.py\nWould load the Mirai model.")
        config_path = DEFAULT_CONFIG_PATH

    with open(config_path, 'r') as f:
        config = json.load(f)

    app = build_app(config)
    return app


if __name__ == '__main__':
    ENV_FILE = os.getenv('ARK_ENV_FILE', None)
    if ENV_FILE:
        dotenv.load_dotenv(ENV_FILE)

    if len(sys.argv) > 1 and sys.argv[1] in {"help", "--help", "-h"}:
        print(__doc__)
        exit(0)

    main()
