import logging
from collections import Iterable

import numpy as np
import pydicom
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut

logger = logging.getLogger('ark')


def apply_windowing(image, center, width, bit_depth=16, voi_type='LINEAR'):
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
        bit_depth (int): Max bit size of pixel
    Returns:
        ndarray: Numpy array of transformed images
    """
    y_min = 0
    y_max = (2**bit_depth - 1)
    y_range = y_max - y_min

    if voi_type == 'LINEAR':
        c = center - 0.5
        w = width - 1.0

        below = image <= (c - w / 2)  # pixels to be set as black
        above = image > (c + w / 2)  # pixels to be set as white
        between = np.logical_and(~below, ~above)

        image[below] = y_min
        image[above] = y_max

        if between.any():
            image[between] = (
                    ((image[between] - c) / w + 0.5) * y_range + y_min
            )
    elif voi_type == 'SIGMOID':
        image = y_range / (1 + np.exp(-4 * (image - center) / width)) + y_min

    return image


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
            logger.warning(e)
            continue

        dicoms.append(dicom)

        if limit is not None and len(dicoms) >= limit:
            logger.debug("Limit of DICOM input reached: {}".format(limit))
            break

    return dicoms


def dicom_to_arr(dicom, auto=True, index=0):
    image = apply_modality_lut(dicom.pixel_array, dicom)

    if (0x0028, 0x1056) in dicom:
        voi_type = dicom[0x0028, 0x1056].value
    else:
        voi_type = 'LINEAR'

    if 'GE' in dicom.Manufacturer:
        image = apply_voi_lut(image.astype(np.uint16), dicom, index=index)

        num_bits = dicom[0x0028, 0x3010].value[index][0x0028, 0x3002].value[2]
        image *= 2**(16 - num_bits)
    elif auto:
        window_center = -600
        window_width = 1500

        image = apply_windowing(image, window_center, window_width, voi_type=voi_type)
    else:
        min_pixel = np.min(image)
        max_pixel = np.max(image)
        window_center = (min_pixel + max_pixel + 1) / 2
        window_width = max_pixel - min_pixel + 1

        image = apply_windowing(image, window_center, window_width, voi_type=voi_type)

    return image.astype(np.uint16)
