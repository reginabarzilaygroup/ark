from api.app import build_app


def main():
    app = build_app()
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
