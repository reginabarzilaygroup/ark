import os
import unittest

import numpy as np
import tensorflow as tf
import torch

from ark.preprocessing import transformers

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class FilterTestCase(unittest.TestCase):
    def setUp(self):
        self.data = np.array([
            [-40, -20],
            [60, 40]
        ])
        self.result = np.array([
            [-1.0, -0.6],
            [1.0, 0.6]
        ])

    def test_subsample(self):
        images = self.data + self.result

        transforms = [
            transformers.SubsampleTransform(sample_size=5),
            transformers.SubsampleTransform(sample_size=1)
        ]

        for transform in transforms:
            sample_size = transform.sample_size

            with self.subTest(sample_size=sample_size):
                result = transform.apply(images)

                self.assertEqual(result.shape[1:], images.shape[1:])
                self.assertEqual(result.shape[0], sample_size)

    def test_scale(self):
        transform = transformers.ScaleTransform(min_scale=-1.0, max_scale=1.0)
        data = transform.apply(self.data)

        self.assertTrue(np.allclose(data, self.result))

    def test_tensor_transform_torch(self):
        images = self.data + self.result

        transform = transformers.TensorTransform(converter='torch')
        tensor = transform.apply(images)

        self.assertTrue(torch.is_tensor(tensor))

    def test_tensor_transform_tf(self):
        images = self.data + self.result

        transform = transformers.TensorTransform(converter='tensorflow')
        tensor = transform.apply(images)

        self.assertTrue(tf.is_tensor(tensor))
