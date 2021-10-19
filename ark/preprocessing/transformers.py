import numpy as np
import tensorflow as tf
import torch


class Transform:
    def apply(self, dicoms):
        raise NotImplementedError


class SubsampleTransform(Transform):
    def __init__(self, sample_size=100):
        self.sample_size = sample_size

    def apply(self, images):
        images_len = images.shape[0]

        if len(images) < self.sample_size:
            pad = self.sample_size - images_len
            left_pad = pad // 2
            right_pad = pad - left_pad

            # pad only the first dimension
            pad_width = [(left_pad, right_pad)] + [(0, 0)] * (len(images.shape) - 1)

            images = np.pad(images, pad_width=pad_width, constant_values=0.0)
        elif len(images) > self.sample_size:
            overflow = images_len - self.sample_size
            remove = list(range(0, images_len + 1, images_len // overflow))[1:]

            images = np.delete(images, remove, axis=0)

        return images


class ShiftTransform(Transform):
    pass


class ScaleTransform(Transform):
    pass


class TensorTransform(Transform):
    converters = {
        'tensorflow': tf.convert_to_tensor,
        'torch': torch.from_numpy
    }

    def __init__(self, converter='torch'):
        if converter in self.converters:
            self.convert = self.converters[converter]
        else:
            raise ValueError("Converter not valid/implemented: {}\nAvailable converts: {}".format(
                converter, self.converters.keys()
            ))

    def apply(self, images):
        return self.convert(images)
