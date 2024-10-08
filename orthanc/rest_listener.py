#!/usr/bin/env python3
import copy
import traceback
from datetime import datetime
import functools
import json
import io
import logging
import os
import sys
from pathlib import Path
import time
from typing import List, Union, Dict, Mapping

import requests
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import generate_uid, BasicTextSRStorage

import api.config
import api.utils
from api import logging_utils
from api.app import set_model
from api.logging_utils import LOGLEVEL_KEY
from api.storage import ARK_SAVE_SCORES_KEY, save_scores

LOGGER_NAME = "orthanc_rest_listener"

script_directory = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(script_directory)
tmp_dir = os.path.join(PROJECT_DIR, "data", "interim", "tmp")

sys.path.append(PROJECT_DIR)


def read_dicom_images(file_paths: List[str]) -> List[pydicom.dataset.FileDataset]:
    """Read DICOM image and return the dataset"""
    return [pydicom.dcmread(file_path) for file_path in file_paths]


def create_structured_report(template_ds: pydicom.dataset.FileDataset, analysis_results,
                             code_meaning="Risk Scores"):
    """
    Create a structured report object from a template DICOM file,
    and store the analysis results in the report.

    :param template_ds:
    :param analysis_results:
    :param code_meaning:
    :return:
    """
    # Create meta-data and data set
    meta = FileMetaDataset()
    basic_sr_uid = "1.2.840.10008.5.1.4.1.1.88.11"  # Basic SR
    meta.MediaStorageSOPClassUID = basic_sr_uid
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # Implicit VR Little Endian

    sr_ds = Dataset()

    # Add essential UIDs
    sr_ds.SOPClassUID = basic_sr_uid
    sr_ds.StudyInstanceUID = template_ds.StudyInstanceUID
    sr_ds.SeriesInstanceUID = template_ds.SeriesInstanceUID

    instance_entropy = [template_ds.StudyInstanceUID, template_ds.SeriesInstanceUID, template_ds.SOPInstanceUID]
    sr_ds.SOPInstanceUID = generate_uid(entropy_srcs=instance_entropy)

    sr_ds.Modality = "SR"

    # Add patient information
    sr_ds.PatientID = template_ds.PatientID
    sr_ds.PatientName = template_ds.PatientName

    # Add study information
    sr_ds.StudyDate = template_ds.StudyDate
    sr_ds.StudyTime = template_ds.StudyTime
    sr_ds.ContentDate = datetime.now().strftime('%Y%m%d')
    sr_ds.ContentTime = datetime.now().strftime('%H%M%S')

    # Create a Referenced Series Sequence
    ref_series_item = Dataset()
    ref_series_item.StudyInstanceUID = template_ds.StudyInstanceUID
    ref_series_item.SeriesInstanceUID = template_ds.SeriesInstanceUID

    sr_ds.ReferencedSeriesSequence = [ref_series_item]

    # Root Content Item (CONTAINER)
    sr_ds.ValueType = 'CONTAINER'
    sr_ds.ContinuityOfContent = 'SEPARATE'
    sr_ds.ConceptNameCodeSequence = [Dataset()]
    sr_ds.ConceptNameCodeSequence[0].CodeValue = '121071'
    sr_ds.ConceptNameCodeSequence[0].CodingSchemeDesignator = 'DCM'
    sr_ds.ConceptNameCodeSequence[0].CodeMeaning = code_meaning

    # Add the 6 numeric results as simple numeric items
    sr_ds.ContentSequence = []
    if isinstance(analysis_results, List):
        analysis_results = {f"Year {idx+1}": result for idx, result in enumerate(analysis_results)}

    for key, value in analysis_results.items():
        item = Dataset()
        item.CodeMeaning = key
        item.ValueType = 'NUM'
        item.RelationshipType = 'CONTAINS'
        item.NumericValue = value

        sr_ds.ContentSequence.append(item)

    sr_file = FileDataset(None, sr_ds, file_meta=meta, preamble=b"\0" * 128)

    return sr_file


def send_dicom_dataset(dcm: Union[str, Path, Dataset], dest_ae_title, dest_host, dest_port,
                       requested_contexts=None):
    """
    Send a DICOM file to an SCP/PACS server.
    Args:
        dcm:
        dest_ae_title:
        dest_host:
        dest_port:
        requested_contexts: default is BasicTextSRStorage (structured report).

    Returns:

    """
    from pynetdicom import AE

    # Initialize the DICOM Application Entity
    my_ae_title = "MY_AE_TITLE"
    ae = AE(ae_title=my_ae_title)

    if requested_contexts is None:
        requested_contexts = [BasicTextSRStorage]
    for context in requested_contexts:
        ae.add_requested_context(context)

    # Initiate association with the PACS
    assoc = ae.associate(dest_host, dest_port, ae_title=dest_ae_title)

    if assoc.is_established:
        status = assoc.send_c_store(dcm)
        logger.debug(f"C-STORE status: {status.Status}")

        # Release the association
        assoc.release()
    else:
        logger.error("Association with PACS failed")


def send_dicom_http(dcm: Dataset, base_url=None, session=None):
    """
    Send a DICOM file over HTTP POST

    Args:
        dcm:
        base_url

    Returns:
        response
    """

    sr_bytes = io.BytesIO()
    dcm.save_as(sr_bytes)
    sr_bytes.seek(0)

    if base_url is None:
        base_url = get_base_url()
    if session is None:
        session = get_orthanc_session()

    logger = logging_utils.get_logger(LOGGER_NAME)

    url = f"{base_url}/instances"
    response = session.post(url, data=sr_bytes)

    if response.status_code == 200:
        logger.debug("Successfully uploaded DICOM SR to Orthanc")
        logger.debug(f"Response: {response.text}")
    else:
        logger.error(f"Failed to upload DICOM SR, status code: {response.status_code}")
        logger.error(f"Response: {response.text}")

    return response


@functools.lru_cache
def get_model():
    config = api.config.get_config()
    set_model(config)
    return config, config["MODEL"]


def get_base_url():
    orthanc_host = os.environ.get("ORTHANC_HOST", "localhost")
    orthanc_http_port = int(os.environ.get("ORTHANC_HTTP_PORT", 8042))
    return f"http://{orthanc_host}:{orthanc_http_port}"


def get_processed_info_dict():
    processed_dict_path = os.environ.get("PROCESSED_DICT_PATH", ".processed_dict.json")
    processed_dict = {"Last": 0}
    if os.path.exists(processed_dict_path):
        with open(processed_dict_path, "r") as f:
            processed_dict = json.load(f)
    return processed_dict_path, processed_dict


def get_changes(since=0, limit=10_000, base_url=None, session=None):
    if base_url is None:
        base_url = get_base_url()

    if session is None:
        session = get_orthanc_session()

    changes = session.get(f"{base_url}/changes?since={since}&limit={limit}")
    changes = changes.json()
    Last = changes["Last"]

    def _change_filter_series(change_dict):
        return change_dict["ChangeType"] == "StableSeries" and change_dict["ResourceType"] == "Series"

    def _change_filter_study(change_dict):
        return change_dict["ChangeType"] == "StableStudy" and change_dict["ResourceType"] == "Study"

    # Whether scans are grouped by Series or Study
    change_type = os.environ.get("ORTHANC_CHANGE_TYPE", "series").lower()
    assert change_type in {"series", "study"}, f"Unknown change_type {change_type}, should be 'series' or 'study'"
    _change_filter = _change_filter_study if change_type == "study" else _change_filter_series

    changes = list(filter(_change_filter, changes["Changes"]))
    return changes, Last


def get_instances_for_group(group_path: str, base_url=None, modalities=None, session=None) -> List[Dict]:
    logger = logging_utils.get_logger(LOGGER_NAME)

    if base_url is None:
        base_url = get_base_url()

    if modalities is None:
        modalities = {"MG", "CT", "OT"}

    if session is None:
        session = get_orthanc_session()

    instances = session.get(f"{base_url}/{group_path}/instances")
    instances = instances.json()

    logger.debug(f"Found {len(instances)} instances in {group_path}")
    # logger.debug(instances)

    if not isinstance(instances, list):
        logger.debug(f"Skipping {group_path} with no instances")
        return []

    all_images = []
    for instance_dict in instances:
        instance_id = instance_dict["ID"]
        instance_file_path = f"instances/{instance_id}/file"

        # Download the DICOM image
        image_bytes = session.get(f"{base_url}/{instance_file_path}").content
        image_buffer = io.BytesIO(image_bytes)
        image_ds = pydicom.dcmread(image_buffer)
        if image_ds.Modality not in modalities:
            logger.debug(f"Skipping instance {instance_id} with modality {image_ds.Modality}")
            continue

        image_buffer.seek(0)
        all_images.append({"ds": image_ds, "bytes": image_bytes,
                           "ID": instance_id})

    return all_images


def process_new_change(model, change_dict: Dict, config: Mapping, session=None) -> List[Dict]:
    logger = logging_utils.get_logger(LOGGER_NAME)
    if session is None:
        session = get_orthanc_session()

    # When a group (series/study) is stable, we can assume that all images are available
    group_id, group_path = change_dict["ID"], change_dict["Path"]

    # Get the list of images in the group
    all_image_instances = get_instances_for_group(group_path, modalities={config["Modality"]})

    if not all_image_instances:
        logger.debug(f"Skipping group {group_id} with no images")
        return []

    min_num_images_dict = {"MG": 4, "CT": 20}
    template_ds = all_image_instances[0]["ds"]
    min_num_images = min_num_images_dict.get(template_ds.Modality, 0)
    if len(all_image_instances) < min_num_images:
        logger.debug(f"Skipping {group_path} with {len(all_image_instances)} < {min_num_images} images")
        return []

    logger.debug(f"Processing {group_path} with {len(all_image_instances)} images")

    ### Perform analysis on the image
    image_bytes = [image_dict["bytes"] for image_dict in all_image_instances]

    # For Mirai, whether to use dcmtk (default) or pydicom for extracting data from file.
    # Sybil always uses pydicom.
    use_pydicom = api.utils.get_environ_bool("ARK_MIRAI_USE_PYDICOM", "false")
    payload = {"dcmtk": not use_pydicom}
    predictions = model.run_model(image_bytes, to_dict=True, payload=payload)

    prediction_scores = predictions["predictions"]
    code_meaning = f"{config['MODEL_NAME'].capitalize()} Risk Scores"
    sr_ds = create_structured_report(template_ds, prediction_scores, code_meaning=code_meaning)

    # Send the structured report back to Orthanc
    response = send_dicom_http(sr_ds, session=session)
    response = json.loads(response.text)

    # Save scores to my own file
    if os.environ.get(ARK_SAVE_SCORES_KEY, "true").lower() == "true":
        addl_info = logging_utils.get_info_dict(config)
        save_scores(template_ds, predictions, addl_info=addl_info)

    # For debugging, delete the SR I just created
    delete_created_sr = False
    if delete_created_sr:
        base_url = get_base_url()
        session.delete(f"{base_url}/instances/{response['ID']}")

    logger.debug(f"Processed series {group_id}")

    return all_image_instances


def delete_multiple_instances(instance_ids: List[str], base_url=None, session=None):
    if base_url is None:
        base_url = get_base_url()
    if session is None:
        session = get_orthanc_session()

    for instance_id in instance_ids:
        instance_path = f"instances/{instance_id}"
        session.delete(f"{base_url}/{instance_path}")

    return len(instance_ids)

@functools.lru_cache
def get_orthanc_session() -> requests.Session:
    username = os.getenv("ORTHANC_USERNAME", "ark")
    password = os.getenv("ORTHANC_PASSWORD", "ark")
    orthanc_auth = (username, password)

    _session = requests.Session()
    _session.auth = orthanc_auth
    return _session

def main():
    api.config.common_setup()

    loglevel = os.environ.get(LOGLEVEL_KEY, "INFO")
    logger = logging_utils.configure_logger(loglevel, LOGGER_NAME)

    # Load model we will use for processing
    config, model = get_model()
    config["Modality"] = "MG" if config["MODEL_NAME"].lower() == "mirai" else "CT"
    logger.debug(f"Model: {config['MODEL_NAME']}")

    polling_interval = os.getenv("ORTHANC_POLLING_INTERVAL", 60)
    session = get_orthanc_session()

    # If set to true, will delete images from Orthanc after processing
    no_store_images = os.getenv("ORTHANC_NO_STORE_IMAGES", "true").lower() == "true"

    # Ping Orthanc to check if it is up
    base_url = get_base_url()
    max_tries = 3
    orthanc_reachable = False
    for _ in range(max_tries):
        try:
            response = session.get(f"{base_url}/system")
            if response.status_code != 200:
                logger.error(f"Orthanc is not available at {base_url}")
                time.sleep(polling_interval)
            else:
                orthanc_reachable = True
                break
        except Exception as e:
            logger.error(f"Error connecting to Orthanc at {base_url}: {e}")
            logger.debug(traceback.format_exc())
            time.sleep(polling_interval)

    if not orthanc_reachable:
        return

    logger.info(f"Orthanc is available at {base_url}")

    while True:
        # Load metadata about the last processed change
        processed_dict_path, processed_dict = get_processed_info_dict()
        Last = processed_dict["Last"]

        try:
            # Retrieve changes from Orthanc
            changes, Last = get_changes(since=Last, session=session)

            if not changes:
                logger.debug("No new changes found")
                time.sleep(polling_interval)
                continue

            # If any relevant changes are found, process them
            for change_dict in changes:
                series_id, change_seq = change_dict["ID"], change_dict["Seq"]

                all_image_instances = process_new_change(model, change_dict, config, session=session)

                # If indicated, delete the images from Orthanc after processing
                if no_store_images:
                    instance_ids = [instance_dict["ID"] for instance_dict in all_image_instances]

                    if instance_ids:
                        logger.info(f"Deleting {len(instance_ids)} instances from series {series_id}")
                        delete_multiple_instances(instance_ids)

            processed_dict["Last"] = Last
            with open(processed_dict_path, "w") as f:
                json.dump(processed_dict, f, indent=2)

        except Exception as e:
            logger.error(f"Error processing changes: {e}")
            logger.error(f"Traceback: {traceback.format_exc(limit=10)}")

        time.sleep(polling_interval)

def main_async():
    import multiprocessing
    process = multiprocessing.Process(target=main)
    process.start()

if __name__ == "__main__":
    main()