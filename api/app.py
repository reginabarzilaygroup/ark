import json
import logging

from flask import Flask
from flask import request

from api.utils import validate_post_request
from api.config import MammoCancerMirai
from model.model import run_model


def build_app(config=None):
    app = Flask('ark')
    logging.getLogger('ark').setLevel(logging.DEBUG)

    if config is not None:
        app.config.from_mapping(config)
    else:
        app.config.from_object(MammoCancerMirai())

    @app.route('/serve', methods=['POST'])
    def dicom():
        """Legacy '/serve' endpoint, replicates same behavior as /dicom.
        # TODO: Remove on 1.0
        """
        app.logger.info("Request received at /serve")
        response = {'data': None, 'message': None, 'statusCode': 200}

        try:
            validate_post_request(request, required=['mrn', 'accession'])
            app.logger.debug("Received JSON payload: {}".format(request.form.to_dict()))
            payload = json.loads(request.form['data'])

            dicom_files = request.files.getlist("files")
            app.logger.debug("Received {} files".format(len(dicom_files)))

            response["data"] = run_model(dicom_files, app.config['ONCONET_ARGS'], payload=payload)
        except Exception as e:
            app.logger.error(e)
            response['message'] = str(e)
            response['statusCode'] = 400

        return response, response['statusCode']

    return app
