import logging
from collections import Iterable

import pydicom


def read_dicoms(dicom_list, limit=None):
    """Reads in a list DICOM files or file paths.

    Args:
        dicom_list (Iterable): List of file objects or file paths
        limit (int, optional): Limit number of dicoms to be read

    Returns:
        list: List of pydicom Datasets
    """
    dicoms = []
    for f in dicom_list:
        try:
            dicom = pydicom.dcmread(f)
        except Exception as e:
            logging.warning(e)
            continue

        dicoms.append(dicom)

        if limit is not None and len(dicoms) >= limit:
            logging.debug("Limit of DICOM input reached: {}".format(limit))
            break

    return dicoms
