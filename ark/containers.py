from collections import Iterable

import numpy as np
from pydicom.pixel_data_handlers.util import apply_modality_lut

import ark
from ark.preprocessing import transformers
from ark.utils import apply_windowing


class DICOMSeries:
    def __init__(self, dicoms, sort=True):
        """Container for a DICOM series.

        Args:
            dicoms (list): List of pydicom Datasets
            sort (bool): If True, will sort the series by its z-coordinates, otherwise the order is unchanged
        """
        if sort:
            self.dicoms = self.z_sort(dicoms)
        else:
            self.dicoms = dicoms

        self.filtrs = []

    @staticmethod
    def z_sort(dicoms):
        """Sort the series by DICOM z-coordinates.

        The z-coordinates are found within the DICOM Image Position (Patient) Attribute, stores as a tuple (x, y, z).
        This attribute is tagged by (0020, 0032). More information can be found in the DICOM standard:
        http://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.2.html#table_C.7-10

        Args:
            dicoms (Iterable): List of pydicom Datasets

        Returns:
            list: List of sorted pydicom Datasets
        """
        return sorted(dicoms, key=lambda dicom: float(dicom[0x0020, 0x0032].value[2]))

    def add_filter(self, filtr):
        """Add a filter to the series container.

        Args:
            filtr (Filter): The ark Filter object to be added
        """
        if not isinstance(filtr, ark.Filter):
            raise TypeError("Not a Filter: {}".format(filtr))

        self.filtrs.append(filtr)

    def add_filters(self, filtrs):
        """Add a list of filters to the series container.

        Args:
            filtrs (Iterable): List of ark Filter objects to be added
        """
        for filtr in filtrs:
            self.add_filter(filtr)

    def apply_filters(self):
        """Apply all filters within the series container to the contained DICOMS, in order as in the list."""
        for filtr in self.filtrs:
            self.dicoms = filtr.apply(self.dicoms)


class DICOMArray:
    def __init__(self, images, window_center=-600, window_width=1500):
        """Container for image pixel arrays.

        Args:
            images (Union[ndarray, list]): Image pixel array or a list of pydicom Datasets that the image pixel array
                will be pulled from
            window_center (float): Window center for DICOM windowing
            window_width (float): Window width for DICOM windowing
        """
        if isinstance(images, np.ndarray):
            self.images = images
        elif isinstance(images, Iterable):
            self.images = self.to_array(images, window_center, window_width)

        self.transforms = []

    @staticmethod
    def to_array(dicoms, window_center, window_width):
        """Extracts pixel arrays from DICOM datasets.

        Args:
            dicoms (Iterable): The pydicom Datasets that the image pixel array will be pulled from
            window_center (float): Window center for DICOM windowing
            window_width (float): Window width for DICOM windowing

        Returns:
            ndarray: Extracted and transformed image pixel array
        """
        arr = []

        for dicom in dicoms:
            dicom = apply_modality_lut(dicom.pixel_array, dicom)
            arr.append(apply_windowing(dicom, window_center, window_width))

        return np.array(arr)

    def add_transform(self, transform):
        """Add a transformation to the array container.

        Args:
            transform (Transform): The ark Transform object to be added
        """
        if not isinstance(transform, ark.Transform):
            raise TypeError("Not a Transform: {}".format(transform))

        self.transforms.append(transform)

    def add_transforms(self, transforms):
        """Add a list of transformations to the array container.

        Args:
            transforms (Iterable): List of ark Transform objects to be added
        """
        for transform in transforms:
            self.add_transform(transform)

    def apply_transforms(self, output_tensor=True, converter='torch'):
        """Apply all transformations within the array container to the pixel array.

        Args:
            output_tensor (bool): If True, will return the pixel array as a tensor, otherwise return nothing
            converter (str): String key that determines what kind of tensor to output
        """
        for transform in self.transforms:
            self.images = transform.apply(self.images)

        if output_tensor:
            transform = transformers.TensorTransform(converter=converter)
            return transform.apply(self.images)
