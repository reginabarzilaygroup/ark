from ark.containers import DICOMArray, DICOMSeries
from ark.preprocessing import filters, transformers
from ark.utils import read_dicoms


def main():
    dicom_dir = './data/1.2.840.113654.2.55.229650531101716203536241646069123704792/'
    dicoms = read_dicoms(dicom_dir, limit=5)
    series = DICOMSeries(dicoms)

    max_thick = 4
    filtrs = [
        filters.FilterSliceThickness(max_thick=max_thick)
    ]
    series.add_filters(filtrs)
    series.apply_filters()

    window_center = -600
    window_width = 1500

    images = DICOMArray(series.dicoms, window_center=window_center, window_width=window_width)

    sample_size = 10
    transforms = [
        transformers.SubsampleTransform(sample_size=sample_size),
        transformers.ScaleTransform(min_scale=0, max_scale=1)
    ]
    images.add_transforms(transforms)

    image_tensor = images.apply_transforms()
    print(image_tensor.shape)


if __name__ == '__main__':
    main()
