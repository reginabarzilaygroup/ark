import argparse
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

    args = parser.parse_args()

    main(args.p, args.config)
