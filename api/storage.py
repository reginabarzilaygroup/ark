import csv
from io import StringIO
import json
import os

from typing import Dict, List, Union, BinaryIO, Tuple

import pydicom

DEFAULT_SAVE_PATH = os.path.expanduser("~/.ark/all_scores.jsonl")
ARK_SAVE_SCORES_KEY = "ARK_SAVE_SCORES"
ARK_SAVE_SCORES_PATH_KEY = "ARK_SAVE_SCORES_PATH"

DICOM_TYPE = Union[str, bytes, BinaryIO]


def extract_dicom_metadata(dicom_file: DICOM_TYPE) -> Dict:
    """
    Extracts and returns Dict of DICOM file metadata such as patient ID, series ID.

    Args:
        dicom_file (str): Path to the DICOM file.

    Returns:
        dict: Dictionary containing extracted metadata.
    """
    ds = pydicom.dcmread(dicom_file)
    meta_keys = ['PatientID', 'AccessionNumber', 'StudyID', 'StudyInstanceUID', 'SeriesInstanceUID']

    metadata = dict()
    for key in meta_keys:
        if key in ds:
            metadata[key] = ds[key].value
    return metadata


def save_scores(dicom_file: DICOM_TYPE, scores_dict: Dict, addl_info: Dict = None):
    save_path = os.environ.get(ARK_SAVE_SCORES_PATH_KEY, DEFAULT_SAVE_PATH)
    save_dir = os.path.dirname(save_path)
    os.makedirs(save_dir, exist_ok=True)

    metadata_dict = extract_dicom_metadata(dicom_file)
    save_dict = scores_dict.copy()
    save_dict.update(metadata_dict)
    if addl_info:
        save_dict.update(addl_info)

    with open(save_path, "a") as f:
        f.write(json.dumps(save_dict) + "\n")


def _expand_list(record: Union[List, Tuple]):
    """Expand list into a dict. Intended for use with predictions"""
    out_dict = dict()
    for i, data in enumerate(record):
        key = f"Year {i+1}"
        out_dict[key] = data
    return out_dict


def _list_dict_csv(data: List[Dict]):
    output = StringIO()
    if data:
        headers = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    return output.getvalue()


def get_csv_from_jsonl(file_path: str):
    final_data = []
    expand_field = "data"

    with open(file_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            final_record = record.copy()
            expand_data = record.pop(expand_field, None)
            if expand_data is not None:
                predictions = expand_data["predictions"]
                if isinstance(predictions, dict):
                    # Mirai-style predictions
                    final_record.update(predictions)
                elif isinstance(predictions, list):
                    # Sybil-style predictions
                    final_record.update(_expand_list(predictions[0][0]))
                del final_record[expand_field]
            final_data.append(final_record)

    return _list_dict_csv(final_data)
