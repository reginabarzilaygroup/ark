import logging

from flask import Flask
from flask import abort, request

from api.utils import validate_post_json, validate_list_paths
from api.config import MammoCancerMirai
from model.model import run_model
from model.utils import read_dicoms


def build_app(config=None):
    app = Flask('ark')

    if config is not None:
        app.config.from_mapping(config)
    else:
        app.config.from_object(MammoCancerMirai())

    @app.route('/serve', methods=['POST'])
    def dicom():
        app.logger.info("Request received at /dicom: {}".format(request.form.to_dict()))
        app.logger.debug(request.form.to_dict())
        try:
            response = {}

            if "dicom" in request.files:
                dicom_list = request.files.getlist("dicom")
            elif request.data:
                validate_post_json(request, required=['paths'])

                payload = request.form.to_dict()['data']
                dicom_list = validate_list_paths(payload['paths'])
            else:
                raise RuntimeError("Request does not contain a JSON body or `files` array upload")

            # dicoms = read_dicoms(dicom_list)
            dicoms = dicom_list
            response["report"] = run_model(dicoms, app.config['ONCONET_ARGS'], request.form.to_dict()['data'])

            return response, 200
        except Exception as e:
            abort(400, description=e)

    return app
