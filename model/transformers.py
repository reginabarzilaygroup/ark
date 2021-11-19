import numpy as np
import torch
import torchvision
from PIL import Image


class Transform:
    def apply(self, img):
        raise NotImplementedError


class Scale2DTransform(Transform):
    def __init__(self, image_size):
        self.transform = torchvision.transforms.Resize((image_size[1], image_size[0]))

    def apply(self, image):
        return self.transform(image)


class AlignLeftTransform(Transform):
    def __init__(self, image_size):
        # Create black image
        mask_r = Image.new('1', image_size)
        # Paint right side in white
        mask_r.paste(1, ((mask_r.size[0] * 3 // 4), 0, mask_r.size[0], mask_r.size[1]))
        mask_l = mask_r.transpose(Image.FLIP_LEFT_RIGHT)

        self.mask_r = mask_r
        self.mask_l = mask_l
        self.black = Image.new('I', image_size)

    def apply(self, image):
        left = image.copy()
        left.paste(self.black, mask=self.mask_l)
        left_sum = np.array(left.getdata()).sum()

        right = image.copy()
        right.paste(self.black, mask=self.mask_r)
        right_sum = np.array(right.getdata()).sum()

        if right_sum > left_sum:
            return image.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            return image


class ToTensorTransform(Transform):
    def __init__(self):
        self.transform = torchvision.transforms.ToTensor()

    def apply(self, image):
        return self.transform(image).float()


class ForceNumChanTensor2DTransform(Transform):
    def __init__(self, num_channels):
        def force_num_chan(tensor):
            existing_chan = tensor.size()[0]

            if not existing_chan == num_channels:
                return tensor.expand(num_channels, *tensor.size()[1:])

            return tensor

        self.transform = torchvision.transforms.Lambda(force_num_chan)

    def apply(self, image):
        return self.transform(image)


class NormalizeTensor2DTransform(Transform):
    def __init__(self, image_mean, image_std):
        channel_means = [image_mean] if len(image_mean) == 1 else image_mean
        channel_stds = [image_std] if len(image_std) == 1 else image_std

        self.transform = torchvision.transforms.Normalize(torch.Tensor(channel_means), torch.Tensor(channel_stds))

    def apply(self, image):
        return self.transform(image)
