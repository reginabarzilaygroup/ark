import tempfile
import unittest
from flask import request

from api.app import build_app
from api.utils import validate_list_paths, validate_post_json


class APIUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = build_app()

    def test_validate_post_json_required(self):
        requirements = [['paths'], ['test', 'paths']]

        with self.app.test_request_context('/dicom', json={'test': 12345}, method='POST'):
            for required in requirements:
                with self.subTest(required=required):
                    self.assertRaises(RuntimeError, validate_post_json, request, required=required)

    def test_validate_post_json_max_size(self):
        with self.app.test_request_context('/dicom', json={'test': 12345}, method='POST'):
            self.assertRaises(RuntimeError, validate_post_json, request, max_size=0)

    def test_validate_post_json_is_json(self):
        with self.app.test_request_context('/dicom', data={'test': 12345}, method='POST'):
            self.assertRaises(RuntimeError, validate_post_json, request)

    def test_validate_list_paths(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertRaises(NotADirectoryError, validate_list_paths, str(f.name))

        self.assertRaises(RuntimeError, validate_list_paths, None)

        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(len(validate_list_paths(d)), 0)
