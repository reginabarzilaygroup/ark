import os
import sys

import api.app
import api.config
from api.config import DEFAULT_CONFIG_PATH, common_setup

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

# Run gunicorn server with Sybil config on port 5000.
gunicorn -b 0.0.0.0:5000 "main:create_app()" --env ARK_CONFIG="api/configs/sybil.json"

# The same thing written slightly differently.
ARK_CONFIG="api/configs/sybil.json" gunicorn -b 0.0.0.0:5000 "main:create_app()"

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
    common_setup()
    config = api.config.get_config()
    app = api.app.build_app(config)
    return app


def _check_help():
    if len(sys.argv) > 1 and sys.argv[1] in {"help", "--help", "-h"}:
        return True
    return False


if __name__ == '__main__':
    if _check_help():
        print(__doc__)
        exit(0)
    main()
