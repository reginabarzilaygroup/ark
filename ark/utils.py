import logging
from collections import Iterable
from pathlib import Path

import numpy as np
import pydicom


def apply_windowing(image, center, width, bit_size=16):
    """Windowing function to transform image pixels for presentation.

    Must be run after a DICOM modality LUT is applied to the image.

    Windowing algorithm defined in DICOM standard:
    http://dicom.nema.org/medical/dicom/2020b/output/chtml/part03/sect_C.11.2.html#sect_C.11.2.1.2

    Reference implementation:
    https://github.com/pydicom/pydicom/blob/da556e33b/pydicom/pixel_data_handlers/util.py#L460

    Args:
        image (ndarray): Numpy image array
        center (float): Window center (or level)
        width (float): Window width
        bit_size (int): Max bit size of pixel

    Returns:
        ndarray: Numpy array of transformed images
    """
    y_min = 0
    y_max = (2**bit_size - 1)
    y_range = y_max - y_min

    c = center - 0.5
    w = width - 1

    below = image <= (c - w / 2)  # pixels to be set as black
    above = image > (c + w / 2)  # pixels to be set as white
    between = np.logical_and(~below, ~above)

    image[below] = y_min
    image[above] = y_max
    if between.any():
        image[between] = (
                ((image[between] - c) / w + 0.5) * y_range + y_min
        )

    return image


def read_dicoms(fp, limit=None):
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

    dicoms = []
    for f in fps:
        try:
            dicom = pydicom.dcmread(f)
            dicoms.append(dicom)

            if limit is not None and len(dicoms) >= limit:
                logging.debug("Limit of DICOM input reachedL {}".format(limit))
                break
        except Exception as e:
            logging.warning(e)

    return dicoms
