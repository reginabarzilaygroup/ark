import unittest
from pathlib import Path

import pydicom

from ark.utils import read_dicoms


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.test_series_dir_path = Path('./ark/test_data/test_series')  # TODO: allow test runner to configure this

    def test_read_dicoms(self):
        fps = [
            str(self.test_series_dir_path),  # str
            self.test_series_dir_path,  # Path
            self.test_series_dir_path.iterdir(),  # Iterable[GeneratorType]
            [fp for fp in self.test_series_dir_path.iterdir()]  # Iterable[list]
        ]

        for fp in fps:
            with self.subTest(fp_type=type(fp)):
                dicoms = read_dicoms(fp)

                dicom_path = next(self.test_series_dir_path.iterdir())
                dicom = pydicom.dcmread(dicom_path)

                self.assertEqual(dicom, dicoms[0], msg="Dicom Datasets do not match")

    def test_read_dicoms_limit(self):
        limit = 2

        with self.subTest(limit=limit):
            dicoms = read_dicoms(self.test_series_dir_path, limit=limit)

            self.assertEqual(len(dicoms), 2)
