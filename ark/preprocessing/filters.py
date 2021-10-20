import sys


class Filter:
    def apply(self, dicoms):
        raise NotImplementedError


class FilterSliceThickness(Filter):
    def __init__(self, min_thick=0, max_thick=sys.maxsize):
        """Sets range for valid slice thickness values.

        Args:
            min_thick (int): Minimum valid slice thickness
            max_thick (int): Maximum valid slice thickness
        """
        self.min_thick = min_thick
        self.max_thick = max_thick

    def apply(self, dicoms):
        """Removes DICOM images that do not fall within the slice thickness range.

        Slice thickness is stored in a DICOM dataset with tag (0018, 0050). For slice thickness see:
        http://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.2.html#table_C.7-10

        Args:
            dicoms (list): List of pydicom Datasets

        Returns:
            valid (list): Filtered list of valid pydicom Datasets
        """
        valid = []

        for dicom in dicoms:
            thickness = float(dicom[0x0018, 0x0050].value)

            if self.min_thick <= thickness <= self.max_thick:
                valid.append(dicom)

        return valid
