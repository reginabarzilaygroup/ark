import io
import json
import unittest
from flask import request

from api.app import build_app
from api.utils import validate_post_request


class APIUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = build_app()
        self.data = {'data': json.dumps({'test': 12345}), 'dicom': [(io.BytesIO(b"12345"), 'test.png')]}

    def test_validate_post_request(self):
        with self.app.test_request_context('/dicom/files', data=self.data, method='POST'):
            validate_post_request(request, required=['test'])

    def test_validate_post_request_missing_required(self):
        with self.app.test_request_context('/dicom/files', data=self.data, method='POST'):
            required = ['notest', 'nottest']
            expected_str = "Missing keys in request JSON: {}".format(required)

            with self.assertRaises(RuntimeError) as cm:
                validate_post_request(request, required=required)

            self.assertEqual(str(cm.exception), expected_str)

    def test_validate_post_request_missing_data(self):
        self.data.pop('data')
        self.data['test'] = 'test'

        with self.app.test_request_context('/dicom/files', data=self.data, method='POST'):
            expected_str = "'data' not in request JSON; {}".format(request.form.keys())

            with self.assertRaises(RuntimeError) as cm:
                validate_post_request(request, required=['test'])

            self.assertEqual(str(cm.exception), expected_str)

    def test_validate_post_request_max_size(self):
        with self.app.test_request_context('/dicom/files', data=self.data, method='POST'):
            max_size = 0
            expected_str = "Request data too large: {} > {}".format(request.content_length, max_size)

            with self.assertRaises(RuntimeError) as cm:
                validate_post_request(request, max_size=max_size)

            self.assertEqual(str(cm.exception), expected_str)

    def test_validate_post_request_missing_dicom(self):
        self.data.pop('dicom')

        with self.app.test_request_context('/dicom/files', data=self.data, method='POST'):
            expected_str = "Request does not contain `dicom` array"

            with self.assertRaises(RuntimeError) as cm:
                validate_post_request(request)

            self.assertEqual(str(cm.exception), expected_str)
