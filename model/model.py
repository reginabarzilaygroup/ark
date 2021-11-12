import logging
import tempfile

import pydicom

import model.onconet_wrapper as onconet
from model.utils import dicom_to_image_dcmtk, dicom_to_arr

logger = logging.getLogger('ark')


def get_dicom_info(dicom):
    view_str = dicom.ViewPosition
    side_str = dicom.ImageLaterality

    valid_view = ['CC', 'MLO']
    valid_side = ['R', 'L']

    if view_str not in valid_view:
        raise ValueError("Invalid View Position `{}`: must be in {}".format(view_str, valid_view))
    if side_str not in valid_side:
        raise ValueError("Invalid Image Laterality `{}`: must be in {}".format(side_str, valid_side))

    view = 0 if view_str == 'CC' else 1
    side = 0 if side_str == 'R' else 1

    return view, side


def run_model(dicom_files, args, payload=None):
    if payload is None:
        payload = {
            'dcmtk': True
        }
    elif 'dcmtk' not in payload:
        payload['dcmtk'] = True

    images = []

    if payload['dcmtk']:
        logger.info('Using dcmtk')
    else:
        logger.info('Using pydicom')

    for dicom in dicom_files:
        try:
            dicom_path = tempfile.NamedTemporaryFile(suffix='.dcm').name
            image_path = tempfile.NamedTemporaryFile(suffix='.png').name
            view, side = get_dicom_info(pydicom.dcmread(dicom))
            dicom.seek(0)
            dicom.save(dicom_path)

            if payload['dcmtk']:
                image = dicom_to_image_dcmtk(dicom_path, image_path)
                logger.debug('Image mode: {}'.format(image.mode))
                images.append({'x': image, 'side_seq': side, 'view_seq': view})
            else:
                dicom = pydicom.dcmread(dicom_path)
                image = dicom_to_arr(dicom, pillow=True)
                images.append({'x': image, 'side_seq': side, 'view_seq': view})
        except Exception as e:
            logger.warning(e)

    risk_factor_vector = None

    y = onconet.process_exam(images, risk_factor_vector, args)

    report = {'predictions': y}

    return report
