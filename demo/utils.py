from subprocess import Popen

import pydicom
from PIL import Image


def dicom_to_image_dcmtk(dicom_path, image_path):
    """Converts a dicom image to a grayscale 16-bit png image using dcmtk.

    Convert DICOM to PNG using dcmj2pnm (support.dcmtk.org/docs/dcmj2pnm.html)
    from dcmtk library (dicom.offis.de/dcmtk.php.en)

    Arguments:
        dicom_path(str): The path to the dicom file.
        image_path(str): The path where the image will be saved.
    """
    default_window_level = "540"
    default_window_width = "580"

    dcm_file = pydicom.dcmread(dicom_path)
    manufacturer = dcm_file.Manufacturer

    # SeriesDescription is not a required attribute, see
    #   https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.3.html#table_C.7-5a
    if hasattr(dcm_file, 'SeriesDescription'):
        ser_desc = dcm_file.SeriesDescription
    else:
        ser_desc = ''

    if 'GE' in manufacturer:
        Popen(['dcmj2pnm', '+on2', '--use-voi-lut', '1', dicom_path, image_path]).wait()
    elif 'C-View' in ser_desc:
        Popen(['dcmj2pnm', '+on2', '+Ww', default_window_level, default_window_width, dicom_path, image_path]).wait()
    else:
        Popen(['dcmj2pnm', '+on2', '--min-max-window', dicom_path, image_path]).wait()

    return Image.open(image_path)
