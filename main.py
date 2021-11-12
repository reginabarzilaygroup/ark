import argparse

from api.app import build_app


def main(p):
    app = build_app()
    app.run(host='0.0.0.0', port=p, debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=5000)

    args = parser.parse_args()

    main(args.p)
