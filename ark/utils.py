import logging
from collections import Iterable
from pathlib import Path

import numpy as np
import pydicom


def apply_windowing(image, center, width, bit_depth=16):
    """ Windowing function for custom DICOM center and width values. Algorithm implementation taken from pydicom:
    https://pydicom.github.io/pydicom/stable/reference/generated/pydicom.pixel_data_handlers.apply_windowing.html#
    """
    y_min = 0
    y_max = (2**bit_depth - 1)
    y_range = y_max - y_min

    c = center - 0.5
    w = width - 1

    below = image <= (c - w / 2)
    above = image > (c + w / 2)
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
        limit (int): limit number of dicoms to be read

    Returns:
        dicoms (list): List of pydicom Datasets
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
