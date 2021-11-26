import logging
import tempfile
import unittest

import pydicom
from pydicom.data import get_testdata_files

from models.utils import read_dicoms


class ModelUtilsTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.ERROR)

        self.fps = get_testdata_files("MR*.dcm")

    def test_read_dicoms_limit(self):
        limit = 2
        dicoms = read_dicoms(self.fps, limit=limit)
        self.assertEqual(len(dicoms), limit, msg="List of dicoms is wrong length")

    def test_read_dicoms_valid(self):
        dicoms = read_dicoms(self.fps + [tempfile.NamedTemporaryFile().name])
        dicoms_bool = [True if isinstance(d, pydicom.Dataset) else False for d in dicoms]
        self.assertTrue(all(dicoms_bool), msg="List of dicoms now all pydicom DataSets")
