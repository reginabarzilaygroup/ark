import io
import json
import os
import traceback
import time
from typing import Mapping, Any, Dict

from flask import Flask, request, send_from_directory, render_template

from api import logging_utils
from api.storage import save_scores, DEFAULT_SAVE_PATH, get_csv_from_jsonl, ARK_SAVE_SCORES_KEY, ARK_SAVE_SCORES_PATH_KEY
from api.utils import dicom_dir_walk, download_zip, validate_post_request
from api.logging_utils import get_info_dict
from models import model_dict


class Args(object):
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)


def set_model(config: Dict[str, Any]):
    model_name = config['MODEL_NAME']
    model_args = config['MODEL_ARGS']
    model_args = Args(model_args)

    if model_name in model_dict:
        config['MODEL'] = model_dict[model_name](model_args)
    else:
        raise KeyError("Model '{}' not found in model dictionary".format(model_name))


def set_routes(app):


    @app.route('/dicom/files', methods=['POST'])
    def dicom():
        """Endpoint to upload physical files
        """
        start = time.time()

        app.logger.info("Request received at /dicom/files")

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

            if os.environ.get(ARK_SAVE_SCORES_KEY, "false").lower() == "true":
                my_dicom = dicom_files[0]
                my_dicom.seek(0)
                dicom_bytes = io.BytesIO(my_dicom.read())
                addl_info = logging_utils.get_info_dict(app.config)
                addl_info.update(payload.get("metadata", {}))
                save_scores(dicom_bytes, response["data"], addl_info=addl_info)

    try:
        dicom_files, payload, return_attentions = _parse_function(response)
        app.logger.debug(f"Payload: {payload}")
        app.logger.debug(f"Return attentions: {return_attentions}")
        response["data"] = _predict_dicom_files(app, model, dicom_files, payload, return_attentions=return_attentions)
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

    @app.route('/scores', methods=['GET'])
    def get_scores():
        """Endpoint to download scores file"""
        try:
            scores_format = request.args.get('format', "jsonl")
            scores_file_path = os.environ.get(ARK_SAVE_SCORES_PATH_KEY, DEFAULT_SAVE_PATH)
            if not os.path.exists(scores_file_path):
                ark_save_scores = os.environ.get(ARK_SAVE_SCORES_KEY, "false")
                msg = f"Scores file not found at {scores_file_path}. "
                msg += "Ensure ARK_SAVE_SCORES=true and ARK_SAVE_SCORES_PATH is set correctly. "
                msg += f"Right now, ARK_SAVE_SCORES={ark_save_scores} and ARK_SAVE_SCORES_PATH={scores_file_path}. "
                return {"message": msg, "statusCode": 404}, 404

            if scores_format == "jsonl":
                base_path = os.path.dirname(scores_file_path)
                filename = os.path.basename(scores_file_path)
                return send_from_directory(base_path, filename, as_attachment=True)
            elif scores_format == "csv":
                csv_data = get_csv_from_jsonl(scores_file_path)
                return csv_data, 200, {'Content-Type': 'text/csv'}
            else:
                raise ValueError(f"Invalid format {scores_format}")

        except Exception as e:
            short_msg = "{}: {}".format(type(e).__name__, e)
            long_msg = traceback.format_exc(limit=10)
            app.logger.error(long_msg)
            response = {'message': short_msg, 'statusCode': 400}
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
            info_dict = get_info_dict(app.config)

            response['data'] = info_dict
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            app.logger.error(msg)
            response['message'] = msg
            response['statusCode'] = 400

        return response, response['statusCode']

    @app.route('/', methods=['GET'])
    @app.route('/home', methods=['GET'])
    @app.route('/index', methods=['GET'])
    def home():
        """Return homepage. Note that routing is order-specific, so we put this last."""
        scores_path = os.environ.get(ARK_SAVE_SCORES_PATH_KEY, DEFAULT_SAVE_PATH)
        show_scores_link = os.path.exists(scores_path)
        return render_template('index.html', show_scores_link=show_scores_link)


def safe_path(base_path, user_input) -> str:
    # Normalize the path to prevent directory traversal
    normalized_path = os.path.normpath(user_input)
    # Restrict to base path
    if os.path.commonpath([base_path, os.path.join(base_path, normalized_path)]) != base_path:
        raise ValueError("Invalid path")
    return str(os.path.join(base_path, normalized_path))


def build_app(config):
    static_folder = os.environ.get('STATIC_FOLDER', "static")
    static_folder = safe_path(os.getcwd(), static_folder)
    app = Flask('ark', static_folder=static_folder)

    app.config.from_mapping(config)
    set_model(app.config)
    set_routes(app)

    return app
