from flask import Flask
from flask import abort, request

from api.utils import validate_post_json, validate_list_paths
from model.model import run_model
from model.utils import read_dicoms


def build_app(config=None):
    app = Flask(__name__)
    if config is not None:
        app.config.from_mapping(config)

    @app.route('/dicom', methods=['POST'])
    def dicom():
        try:
            response = {}

            if "files" in request.files:
                dicom_list = request.files.getlist("files")
            elif request.data:
                validate_post_json(request, required=['paths'])

                payload = request.get_json()
                dicom_list = validate_list_paths(payload['paths'])
            else:
                raise RuntimeError("Request does not contain a JSON body or `files` array upload")

            dicoms = read_dicoms(dicom_list)
            response["report"] = run_model(dicoms)

            return response, 200
        except Exception as e:
            abort(400, description=e)

    return app
