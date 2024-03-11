import argparse
import json
import os

import dotenv

from api.app import build_app


# TODO: support dev/prod envs
def main(port, config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)

    app = build_app(config)
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=None, dest="port", type=int)
    parser.add_argument('--config', default="api/configs/empty.json")
    parser.add_argument('--env-file', default=None)

    args = parser.parse_args()
    if args.env_file:
        dotenv.load_dotenv(args.env_file)

    _port = args.port or int(os.getenv('ARK_PORT', 5000))

    main(_port, args.config)
