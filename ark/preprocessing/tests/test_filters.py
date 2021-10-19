import unittest

from ark.preprocessing import filters
from ark.utils import read_dicoms


class FilterTestCase(unittest.TestCase):
    def setUp(self):
        test_series_dir_path = './ark/test_data/test_series/'  # TODO: allow test runner to configure this
        self.dicoms = read_dicoms(test_series_dir_path, limit=2)

    def test_filter_slice_thickness(self):
        slice_values = []

        for i, dicom in enumerate(self.dicoms):
            slice_elem = dicom[0x0018, 0x0050]
            slice_elem.value = i
            slice_values.append(float(dicom[0x0018, 0x0050].value))

        slice_min = min(slice_values)
        slice_max = max(slice_values)

        filtrs = [
            filters.FilterSliceThickness(min_thick=slice_max),
            filters.FilterSliceThickness(max_thick=slice_min)
        ]

        for filtr in filtrs:
            min_thick = filtr.min_thick
            max_thick = filtr.max_thick

            with self.subTest(min_thick=min_thick, max_thick=max_thick):
                self.assertEqual(len(filtr.apply(self.dicoms)), 1)
