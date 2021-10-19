from collections import Iterable

import numpy as np
from pydicom.pixel_data_handlers.util import apply_modality_lut

from ark.preprocessing import filters, transformers
from ark.utils import apply_windowing


class DICOMSeries:
    # container for pydicom datasets

    def __init__(self, dicoms, sort=True):
        if sort:
            self.dicoms = self.z_sort(dicoms)
        else:
            self.dicoms = dicoms

        self.filtrs = []

    @staticmethod
    def z_sort(dicoms):
        return sorted(dicoms, key=lambda dicom: float(dicom[0x0020, 0x0032].value[2]))

    def add_filter(self, filtr):
        if not isinstance(filtr, filters.Filter):
            raise TypeError("Not a Filter: {}".format(filtr))

        self.filtrs.append(filtr)

    def add_filters(self, filtrs):
        for filtr in filtrs:
            self.add_filter(filtr)

    def apply_filters(self):
        for filtr in self.filtrs:
            self.dicoms = filtr.apply(self.dicoms)


class DICOMArray:
    # container for DICOM pixel arrays
    def __init__(self, images, window_center=-600, window_width=1500):
        if isinstance(images, np.ndarray):
            self.images = images
        elif isinstance(images, Iterable):
            self.images = self.to_array(images, window_center, window_width)

        self.transforms = []

    @staticmethod
    def to_array(dicoms, window_center, window_width):
        arr = []

        for dicom in dicoms:
            dicom = apply_modality_lut(dicom.pixel_array, dicom)
            arr.append(apply_windowing(dicom, window_center, window_width))

        return np.array(arr)

    def add_transform(self, transform):
        if not isinstance(transform, transformers.Transform):
            raise TypeError("Not a Transform: {}".format(transform))

        self.transforms.append(transform)

    def add_transforms(self, transforms):
        for transform in transforms:
            self.add_transform(transform)

    def apply_transform(self):
        for transform in self.transforms:
            self.images = transform.apply(self.images)
