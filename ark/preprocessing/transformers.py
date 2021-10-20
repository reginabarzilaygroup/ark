import numpy as np
import tensorflow as tf
import torch


class Transform:
    def apply(self, dicoms):
        raise NotImplementedError


class SubsampleTransform(Transform):
    def __init__(self, sample_size=100):
        """Sets target size of DICOM image array.

        Args:
            sample_size (int): Target size of image array
        """
        self.sample_size = sample_size

    def apply(self, images):
        """Either pads or truncates array to target sample size.

        Args:
            images (ndarray): DICOM image numpy array

        Returns:
            images (ndarray): Padded or truncated numpy array
        """
        images_len = images.shape[0]

        if len(images) < self.sample_size:
            pad = self.sample_size - images_len
            left_pad = pad // 2
            right_pad = pad - left_pad

            # pad only the first dimension
            pad_width = [(left_pad, right_pad)] + [(0, 0)] * (len(images.shape) - 1)

            images = np.pad(images, pad_width=pad_width, constant_values=0.0)
        elif len(images) > self.sample_size:
            remove = np.round(np.linspace(0, images_len - 1, self.sample_size)).astype(int)
            images = np.delete(images, remove, axis=0)

        return images


class ShiftTransform(Transform):
    pass


class ScaleTransform(Transform):
    def __init__(self, min_scale=0.0, max_scale=1.0):
        """Sets range in which to scale array values.

        Args:
            min_scale (float): Lower bound of scale
            max_scale (float): Upper bound of scale
        """
        self.min_scale = min_scale
        self.max_scale = max_scale

    def apply(self, images):
        images = (images - images.min()) / (images.max() - images.min())
        return (self.max_scale - self.min_scale) * images + self.min_scale


class TensorTransform(Transform):
    converters = {
        'tensorflow': tf.convert_to_tensor,
        'torch': torch.from_numpy
    }

    def __init__(self, converter='torch'):
        """Sets the type of tensor that will be returned by the transformation.

        Args:
            converter (str): String key that defines what kind of tensor to create
        """
        if converter in self.converters:
            self.convert = self.converters[converter]
        else:
            raise ValueError("Converter not valid/implemented: {}\nAvailable converts: {}".format(
                converter, self.converters.keys()
            ))

    def apply(self, images):
        """Converts a numpy image array to a tensor.

        Args:
            images (ndarray): Numpy image array to be transformed

        Returns:
            images (Union[tf.Tensor, torch.Tensor]): Converted image tensor
        """
        return self.convert(images)
