import os
import unittest

import tensorflow as tf
import torch

from ark.containers import DICOMArray
from ark.preprocessing import transformers
from ark.utils import read_dicoms

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class FilterTestCase(unittest.TestCase):
    def setUp(self):
        window_center = -600
        window_width = 1500
        test_series_dir_path = './ark/test_data/test_series/'  # TODO: allow test runner to configure this

        self.images = DICOMArray.to_array(
            read_dicoms(test_series_dir_path, limit=5), window_center=window_center, window_width=window_width
        )

    def test_subsample(self):
        transforms = [
            transformers.SubsampleTransform(sample_size=10),
            transformers.SubsampleTransform(sample_size=5)
        ]

        for transform in transforms:
            sample_size = transform.sample_size

            with self.subTest(sample_size=sample_size):
                self.assertEqual(transform.apply(self.images).shape[0], sample_size)

    def test_tensor_transform_torch(self):
        transform = transformers.TensorTransform(converter='torch')
        tensor = transform.apply(self.images)

        self.assertTrue(torch.is_tensor(tensor))

    def test_tensor_transform_tf(self):
        transform = transformers.TensorTransform(converter='tensorflow')
        tensor = transform.apply(self.images)

        self.assertTrue(tf.is_tensor(tensor))
