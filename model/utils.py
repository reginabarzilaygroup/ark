import logging
from collections import Iterable
from pathlib import Path

import pydicom


def read_dicoms(dicom_list, limit=None):
    """Reads in DICOM files a list.

    Args:
        dicom_list (Iterable): List of filepaths or byte arrays
        limit (int, optional): Limit number of dicoms to be read

    Returns:
        list: List of pydicom Datasets
    """
    dicoms = []
    for f in dicom_list:
        try:
            dicom = pydicom.dcmread(f)
            dicoms.append(dicom)

            if limit is not None and len(dicoms) >= limit:
                logging.debug("Limit of DICOM input reached: {}".format(limit))
                break
        except Exception as e:
            logging.warning(e)

    return dicoms


def read_dicom_paths(fp, limit=None):
    """Reads in DICOM files from a valid directory or list of file paths.

    Args:
        fp (Union[str, Iterable]): Path to directory of DICOMs or list of file paths pointing to DICOMs
        limit (int, optional): Limit number of dicoms to be read

    Returns:
        list: List of pydicom Datasets
    """

    if isinstance(fp, str) or isinstance(fp, Path):
        fps = Path(fp)

        if fps.is_dir():
            fps = list(fps.iterdir())
        else:
            raise NotADirectoryError("Not a directory: {}".format(fps))
    elif isinstance(fp, Iterable):
        fps = [Path(f) for f in fp]
    else:
        raise Exception("Input is not a valid string or list of file paths: {}".format(fp))

    dicoms = read_dicoms(fps, limit=limit)

    return dicoms


def read_dicom_bytes(dicom_arrays, limit=None):
    """Reads DICOMs from list of byte arrays.

    Args:
        dicom_arrays (Iterable[bytes]): List if DICOM byte arrays
        limit (int, optional): Limit number of dicoms to be read

    Returns:
        list: List of pydicom Datasets
    """

    if all([isinstance(a, bytes) for a in dicom_arrays]):
        dicoms = read_dicoms(dicom_arrays, limit=limit)
    else:
        raise TypeError("Input list contents not all bytes")

    return dicoms
