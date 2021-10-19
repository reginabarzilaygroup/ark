import numpy as np


class Transform:
    def apply(self, dicoms):
        raise NotImplementedError


class SubsampleTransform(Transform):
    def __init__(self, sample_size=100):
        self.sample_size = sample_size

    def apply(self, dicoms):
        dicoms_len = dicoms.shape[0]

        if len(dicoms) < self.sample_size:
            pad = self.sample_size - dicoms_len
            left_pad = pad // 2
            right_pad = pad - left_pad

            # pad only the first dimension
            pad_width = [(left_pad, right_pad)] + [(0, 0)] * (len(dicoms.shape) - 1)

            dicoms = np.pad(dicoms, pad_width=pad_width, constant_values=0.0)
        elif len(dicoms) > self.sample_size:
            overflow = dicoms_len - self.sample_size
            remove = list(range(0, dicoms_len + 1, dicoms_len // overflow))[1:]

            dicoms = np.delete(dicoms, remove, axis=0)

        return dicoms


class ShiftTransform(Transform):
    pass


class ScaleTransform(Transform):
    pass


class TensorTransform(Transform):
    pass
