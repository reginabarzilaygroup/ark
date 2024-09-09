import io
import json
import os
import traceback
import time
from typing import Mapping, Any, Dict

from flask import Flask, request, send_from_directory, render_template
import werkzeug.datastructures

import pydicom
import pydicom.uid

import api.utils
from api import logging_utils
from api.storage import save_scores, DEFAULT_SAVE_PATH, get_csv_from_jsonl, ARK_SAVE_SCORES_KEY, ARK_SAVE_SCORES_PATH_KEY
from api.utils import dicom_dir_walk, download_zip, validate_post_request, get_environ_bool
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

def _parse_multipart(response):
    """
    Parse a multipart DICOM file upload, as done in DICOMweb STOW-RS.
    Args:
        app:

    Returns:

    """
    # Get the boundary from the content-type header
    content_type = request.headers['Content-Type']
    boundary = content_type.split("boundary=")[-1]
    boundary = boundary.encode()

    raw_data = request.get_data()
    parts = raw_data.split(b"--" + boundary)

    # Only keep parts with the appropriate key
    keep_key = b"Content-Type: application/dicom"

    dicom_files = []
    idx = 0
    for part in parts:

        # Only keep parts with the appropriate key
        if keep_key not in part:
            continue

        # Find the start of the DICOM data
        dicom_start = part.find(b'\r\n\r\n') + 4
        if dicom_start == -1:
            continue
        dicom_bytes = part[dicom_start:]

        # Remove any trailing whitespace characters
        rem_chars = [b"\r\n", b"\n\r", b"\r", b"\n"]
        for rr in rem_chars:
            dicom_bytes = dicom_bytes.rstrip(rr)

        dicom_file = io.BytesIO(dicom_bytes)
        dicom_file.seek(0)
        filename = f"{idx}.dcm"
        file_storage = werkzeug.datastructures.FileStorage(stream=dicom_file, filename=filename)
        dicom_files.append(file_storage)
        idx += 1

    return dicom_files, {}, False

def _parse_form_request(response):
    payload = json.loads(request.form.get("data", "{}"))
    if 'metadata' in payload:
        response['metadata'] = payload['metadata']

    # Return attentions if set by env variable, which can be overridden by the payload
    return_attentions = api.utils.get_environ_bool("ARK_RETURN_ATTENTIONS", "false")
    if "return_attentions" in payload:
        return_attentions = payload["return_attentions"]

    dicom_files = request.files.getlist("dicom")

    return dicom_files, payload, return_attentions

def _predict_wrapper(app, _parse_function):
    model = app.config['MODEL']
    start = time.time()
    response = {'data': None, 'metadata': None, 'message': None, 'statusCode': 200}
    dicom_files = []

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

    return response, response['statusCode'], dicom_files

def _predict_dicom_files(app, model, dicom_files, payload, **kwargs):
    app.logger.debug("Received {} dicom files".format(len(dicom_files)))

    data = model.run_model(dicom_files, payload=payload, **kwargs)

    if get_environ_bool(ARK_SAVE_SCORES_KEY):
        my_dicom = dicom_files[0]
        my_dicom.seek(0)
        dicom_bytes = io.BytesIO(my_dicom.read())
        addl_info = logging_utils.get_info_dict(app.config)
        addl_info.update(payload.get("metadata", {}))
        save_scores(dicom_bytes, data, addl_info=addl_info)

    return data

def _get_uid_dict(dicom_file):
    dicom_file.seek(0)
    dcm = pydicom.dcmread(dicom_file)
    dicom_file.seek(0)

    return {
        "00081155": {"vr": "UI", "Value": [dcm.StudyInstanceUID]},
        "00081150": {"vr": "UI", "Value": [dcm.SOPClassUID]},
    }

def set_routes(app):

    @app.route('/dicom/files', methods=['POST'])
    def dicom():
        """Endpoint to upload physical files
        """
        app.logger.debug("Request received at /dicom/files")
        model = app.config['MODEL']
        validate_post_request(request, required=model.required_data)
        response, response_code, dicom_files = _predict_wrapper(app, _parse_form_request)
        return response, response_code

    @app.route('/dicom-web/studies', methods=['POST'])
    @app.route('/dicom-web/studies/<study_instance_uid>', methods=['POST'])
    def handle_store(study_instance_uid=None):
        app.logger.debug("Request received at /dicom-web/studies")
        if study_instance_uid is not None:
            app.logger.debug(f"Request received at /dicom-web/studies/{study_instance_uid}")

        if 'multipart/related' not in request.content_type:
            return "Invalid content type\n", 400

        response, response_code, dicom_files =  _predict_wrapper(app, _parse_multipart)

        # Add study information to the response
        processed_studies = [_get_uid_dict(dicom_file) for dicom_file in dicom_files]

        success_studies = processed_studies
        failed_studies = []
        if 400 <= response_code < 500:
            success_studies = []
            failed_studies = processed_studies

        stow_response = {
            # URLs where the study is accessible via WADO. Currently not supported.
            "00081190": {
                "vr": "UR",
                "Value": []
            },
            # Studies processed successfully
            "00081199": {
                "vr": "SQ",
                "Value": success_studies
            },
            # Studies that failed to process
            "00081198": {
                "vr": "SQ",
                "Value": failed_studies
            },
            "data": response["data"]
        }

        return stow_response, response_code

    @app.route('/scores', methods=['GET'])
    def get_scores():
        """Endpoint to download scores file"""
        try:
            scores_format = request.args.get('format', "jsonl")
            scores_file_path = os.environ.get(ARK_SAVE_SCORES_PATH_KEY, DEFAULT_SAVE_PATH)
            if not os.path.exists(scores_file_path):
                ark_save_scores = get_environ_bool(ARK_SAVE_SCORES_KEY)
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
