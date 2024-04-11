import json
import logging
import os
import threading
import traceback
import time

from flask import Flask, request, send_from_directory

from api import __version__ as api_version
from api.utils import dicom_dir_walk, download_zip, validate_post_request
from api.logging import async_log_analytics, get_info_dict
from models import model_dict


def set_model(app):
    model_name = app.config['MODEL_NAME']
    model_args = app.config['MODEL_ARGS']

    if model_name in model_dict:
        app.config['MODEL'] = model_dict[model_name](model_args)
    else:
        raise KeyError("Model '{}' not found in model dictionary".format(model_name))


def set_routes(app):

    @app.route('/serve', methods=['POST'])  # TODO: Legacy endpoint, remove on 1.0
    @app.route('/dicom/files', methods=['POST'])
    def dicom():
        """Endpoint to upload physical files
        """
        start = time.time()

        app.logger.info("Request received at /dicom/files")
        # async_log_analytics(app, {"url": "/dicom/files"})

        response = {'data': None, 'metadata': None, 'message': None, 'statusCode': 200}
        model = app.config['MODEL']

        try:
            validate_post_request(request, required=model.required_data)

            app.logger.debug("Received JSON payload: {}".format(request.form.to_dict()))
            payload = json.loads(request.form.get("data", "{}"))
            if 'metadata' in payload:
                response['metadata'] = payload['metadata']

            dicom_files = request.files.getlist("dicom")
            app.logger.debug("Received {} valid files".format(len(dicom_files)))

            response["data"] = model.run_model(dicom_files, payload=payload)
        except Exception as e:
            short_msg = "{}: {}".format(type(e).__name__, e)
            long_msg = traceback.format_exc(limit=10)
            app.logger.error(long_msg)
            response['message'] = short_msg
            response['statusCode'] = 400

        runtime = "{:.2f}s".format(time.time() - start)
        response['runtime'] = "{:.2f}s".format(time.time() - start)
        app.logger.debug("Request completed in {}".format(runtime))

        return response, response['statusCode']

    @app.route('/dicom/uri', methods=['POST'])
    def dicom_uri():
        """Endpoint to send a link to an archive file containing DICOM files
        """
        start = time.time()

        app.logger.info("Request received at /dicom/uri")
        # async_log_analytics(app, {"url": "/dicom/uri"})

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

    @app.route('/info', methods=['GET'])
    def info():
        """Endpoint to return general info of the API
        """
        app.logger.info("Request received at /info")
        # async_log_analytics(app, {"url": "/info"})

        response = {'data': None, 'message': None, 'statusCode': 200}

        try:
            info_dict = get_info_dict(app)

            response['data'] = info_dict
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            app.logger.error(msg)
            response['message'] = msg
            response['statusCode'] = 400

        return response, response['statusCode']

    @app.route('/home', methods=['GET'])
    @app.route('/index', methods=['GET'])
    def home():
        """Return homepage. Note that routing is order-specific, so we put this last."""
        return send_from_directory(app.static_folder, 'index.html')


def build_app(config):
    app = Flask('ark', static_folder=os.environ.get('STATIC_FOLDER', "static"))
    app.config.from_mapping(config)
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logger = logging.getLogger('ark')
    logger.setLevel(log_level)
    logger.propagate = False

    app.config['API_VERSION'] = api_version
    set_model(app)
    set_routes(app)

    return app
