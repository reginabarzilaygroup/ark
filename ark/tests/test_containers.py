import unittest

from ark.containers import DICOMSeries
from ark.preprocessing import filters
from ark.utils import read_dicoms


class DICOMSeriesTestCase(unittest.TestCase):
    def setUp(self):
        test_series_dir_path = './ark/test_data/test_series/'  # TODO: allow test runner to configure this
        self.dicoms = read_dicoms(test_series_dir_path)
        self.series = DICOMSeries(self.dicoms)

        self.flters = [
            filters.FilterSliceThickness(),
            filters.FilterSliceThickness()
        ]

    def test_z_sort(self):
        z_values = []

        for dicom in self.series.dicoms:
            z_values.append(float(dicom[0x0020, 0x0032].value[2]))

        bools = [z_values[i] <= z_values[i+1] for i in range(len(z_values) - 1)]

        self.assertTrue(all(bools))

    def test_add_filter(self):
        self.series.add_filter(self.flters[0])

        self.assertEqual(len(self.series.filtrs), 1)

    def test_add_filters(self):
        self.series.add_filters(self.flters)

        self.assertEqual(len(self.series.filtrs), 2)

    def test_apply_filters(self):
        self.series.add_filters(self.flters)
        self.series.apply_filters()
