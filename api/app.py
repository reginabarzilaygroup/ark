import json
import logging
import time

from flask import Flask
from flask import request

import models
from api.utils import dicom_dir_walk, download_zip, validate_post_request


def set_model(app):
    model_name = app.config['MODEL_NAME']
    model_args = app.config['ONCONET_ARGS']

    app.config['MODEL'] = models.model_dict[model_name](model_args)


def build_app(config):
    app = Flask('ark')
    app.config.from_mapping(config)
    logging.getLogger('ark').setLevel(logging.DEBUG)

    set_model(app)

    @app.route('/serve', methods=['POST'])  # TODO: Legacy endpoint, remove on 1.0
    @app.route('/dicom/files', methods=['POST'])
    def dicom():
        """Endpoint to upload physical files
        """
        start = time.time()

        app.logger.info("Request received at /dicom/files")
        response = {'data': None, 'message': None, 'statusCode': 200}
        model = app.config['MODEL']

        try:
            validate_post_request(request, required=model.required_data)

            app.logger.debug("Received JSON payload: {}".format(request.form.to_dict()))
            payload = json.loads(request.form['data'])

            dicom_files = request.files.getlist("dicom")
            # TODO: Must receive four files
            app.logger.debug("Received {} files".format(len(dicom_files)))

            response["data"] = model.run_model(dicom_files, payload=payload)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            app.logger.error(msg)
            response['message'] = msg
            response['statusCode'] = 400

        response['runtime'] = "{:.2f}s".format(time.time() - start)

        return response, response['statusCode']

    @app.route('/dicom/uri', methods=['POST'])
    def dicom_uri():
        """Endpoint to send a link to an archive file containing DICOM files
        """
        start = time.time()

        app.logger.info("Request received at /dicom/uri")
        response = {'data': None, 'message': None, 'statusCode': 200}
        model = app.config['MODEL']

        try:
            payload = request.get_json()
            app.logger.debug("Received JSON payload: {}".format(payload))

            download_zip(payload['uri'])
            dicom_files = dicom_dir_walk()

            response["data"] = model.run_model(dicom_files, payload=payload)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            app.logger.error(msg)
            response['message'] = msg
            response['statusCode'] = 400

        response['runtime'] = "{:.2f}s".format(time.time() - start)

        return response, response['statusCode']

    return app
