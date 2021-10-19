import sys


class Filter:
    def apply(self, dicoms):
        raise NotImplementedError


class FilterSliceThickness(Filter):
    def __init__(self, min_thick=0, max_thick=sys.maxsize):
        self.min_thick = min_thick
        self.max_thick = max_thick

    def apply(self, dicoms):
        valid = []

        for dicom in dicoms:
            thickness = float(dicom[0x0018, 0x0050].value)

            if self.min_thick <= thickness <= self.max_thick:
                valid.append(dicom)

        return valid
