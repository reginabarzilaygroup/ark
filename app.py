from flask import Flask
from flask import abort, request

from model.model import run_model
from model.utils import read_dicom_bytes, read_dicom_paths


def validate_post_json(req, required=None, max_size=8 * 10**6):
    msg = None
    if required is None:
        required = []

    if req.content_length > max_size:
        msg = "POST data too large: {} > {}".format(req.content_length, max_size)
    elif req.is_json:
        data = req.get_json()
        invalid = []

        for item in required:
            if item not in data:
                invalid.append(item)

        if not invalid:
            return msg
        else:
            msg = "Invalid/missing arguments in JSON: {}".format(invalid)
    else:
        msg = "POST data not JSON: {}".format(req.get_data())

    return msg


def build_app():
    app = Flask(__name__)

    @app.route('/dicom/paths', methods=['POST'])
    def dicom_paths():
        required = ['paths']

        msg = validate_post_json(request, required=required)
        if msg is not None:
            abort(400, msg)

        payload = request.get_json()
        dicoms = read_dicom_paths(payload['paths'])

        report = run_model(dicoms)

        return {"report": report}, 200

    @app.route('/dicom/bytes', methods=['POST'])
    def dicom_bytes():
        required = ['bytes']

        msg = validate_post_json(request, required=required)
        if msg is not None:
            abort(400, msg)

        payload = request.get_json()
        dicoms = read_dicom_bytes(payload['bytes'])

        report = run_model(dicoms)

        return {"report": report}, 200

    return app


if __name__ == '__main__':
    api = build_app()

    api.run(host='0.0.0.0', port=8080)
