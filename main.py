import argparse
import dotenv
import json

from api.app import build_app


# TODO: support dev/prod envs
def main(port, config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)

    app = build_app(config)
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=5000)
    parser.add_argument('--config', default="api/configs/empty.json")
    parser.add_argument('--env-file', default=None)

    args = parser.parse_args()
    if args.env_file:
        dotenv.load_dotenv(args.env_file)

    main(args.p, args.config)
