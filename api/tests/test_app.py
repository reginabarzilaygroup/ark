import unittest

from pydicom.data import get_testdata_files

from api.app import build_app


class APIAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = build_app({'TESTING': True})
        self.client = self.app.test_client()
        self.fps = get_testdata_files('MR*.dcm')

    def test_dicom_files(self):
        files = [open(fp, 'rb') for fp in self.fps]

        rv = self.client.post('/dicom', data={'files': files})

        for f in files:
            f.close()

        self.assertEqual(rv.status_code, 200)

    def test_dicom_paths(self):
        rv = self.client.post('/dicom', json={'paths': self.fps})

        self.assertEqual(rv.status_code, 200)

    def test_dicom_invalid(self):
        rv = self.client.post('/dicom', data={})

        self.assertEqual(rv.status_code, 400)
