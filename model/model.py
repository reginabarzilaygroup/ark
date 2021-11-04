import logging

import numpy as np
from PIL import Image

import model.onconet_wrapper as onconet
import model.oncoqueries_wrapper as oncoqueries
from model.utils import dicom_to_arr

logger = logging.getLogger('ark')


def get_info(dicom):
    view_str = dicom.ViewPosition
    side_str = dicom.ImageLaterality

    valid_view = ['CC', 'MLO']
    valid_side = ['R', 'L']

    if view_str not in valid_view:
        raise ValueError("Invalid View Position `{}`: must be in {}".format(view_str, valid_view))
    if side_str not in valid_side:
        raise ValueError("Invalid Image Laterality `{}`: must be in {}".format(side_str, valid_side))

    return valid_view.index(view_str), valid_side.index(side_str)


def run_model(dicoms, args, metadata):
    report = {"testData": 123, "dicomsLen": len(dicoms)}
    dicom_path = '/tmp/tmp.dcm'
    image_path = '/tmp/tmp.png'
    try:
        images = []

        for dicom in dicoms:
            dicom.save(dicom_path)

            import pydicom
            view, side = get_info(pydicom.dcmread(dicom_path))
            # image = dicom_to_arr(dicom)

            from subprocess import Popen
            Popen(['dcmj2pnm', '-O', '+on2', '--use-voi-lut', '1', dicom_path, image_path]).wait()

            images.append({'x': Image.open(image_path), 'side_seq': side, 'view_seq': view})
            # images.append({'x': Image.fromarray(image, mode='I'), 'side_seq': side, 'view_seq': view})

        if args.use_risk_factors and not args.use_pred_risk_factors_at_test:
            assert 'mrn' in metadata
            assert 'accession' in metadata
            logger.info('Get risks')
            risk_factor_vector = oncoqueries.get_risk_factors(args,
                                                              metadata['mrn'],
                                                              metadata['accession'],
                                                              args.temp_img_dir,
                                                              logger)
        else:
            risk_factor_vector = None

        y = onconet.process_exam(images, risk_factor_vector, args)

        report = {'predictions': y}
    except ValueError as e:
        logger.warning(e)

    return report
