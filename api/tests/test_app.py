import json
import unittest

from pydicom.data import get_testdata_files

from api.app import build_app


class APIAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = build_app({'TESTING': True})
        self.client = self.app.test_client()
        self.fps = get_testdata_files('MR_small*.dcm')
        self.data = {'mrn': '2553222', 'accession': '12117409'}

    def test_files_upload(self):
        files = [open(fp, 'rb') for fp in self.fps]

        rv = self.client.post('/serve', data={'dicom': files, 'data': json.dumps(self.data)})

        for f in files:
            f.close()

        self.assertEqual(rv.status_code, 200)

    def test_files_none_message(self):
        rv = self.client.post('/serve', data={'data': json.dumps(self.data)})

        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.json['message'], "Request does not contain `dicom` array")
