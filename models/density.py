import logging
import tempfile

import numpy as np
import pydicom
import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F

import onconet.transformers.factory as transformer_factory
from models.base import BaseModel, ArgsDict
from models.utils import dicom_to_image_dcmtk, dicom_to_arr
from onconet.transformers.basic import ComposeTrans
from onconet.utils import parsing

logger = logging.getLogger('ark')


class DensityModel(BaseModel):
    def __init__(self, args):
        super().__init__()
        self.args = ArgsDict(args)
        self.required_data = None

    def load_model(self):
        logger.info("Loading model...")
        self.args.cuda = self.args.cuda and torch.cuda.is_available()

        model = torch.load(self.args.snapshot, map_location='cpu')

        # Unpack models taht were trained as data parallel
        if isinstance(model, nn.DataParallel):
            model = model.module

        # Version mismatch workaround
        model._model.args.survival_analysis_setup = self.args.survival_analysis_setup
        model._model.args.pred_risk_factors = self.args.pred_risk_factors

        # Add use precomputed hiddens for models trained before it was introduced.
        # Assumes a resnet WHybase backbone
        try:
            model._model.args.use_precomputed_hiddens = self.args.use_precomputed_hiddens
            model._model.args.cuda = self.args.cuda
        except Exception as e:
            logger.debug("Exception caught, skipping precomputed hiddens")
            pass

        return model

    def label_map(self, pred):
        pred = pred.argmax()
        density_labels = [1, 2, 3, 4]
        return density_labels[pred]

    def process_image(self, image, model, risk_factor_vector=None):
        logger.info("Processing image...")

        test_image_transformers = parsing.parse_transformers(self.args.test_image_transformers)
        test_tensor_transformers = parsing.parse_transformers(self.args.test_tensor_transformers)
        test_transformers = transformer_factory.get_transformers(test_image_transformers, test_tensor_transformers, self.args)
        transforms = ComposeTrans(test_transformers)

        ## Apply transformers
        x = transforms(image, self.args.additional)
        x = autograd.Variable(x.unsqueeze(0))
        risk_factors = autograd.Variable(risk_factor_vector.unsqueeze(0)) if risk_factor_vector is not None else None
        logger.debug("Image size: {}".format(x.size()))

        if self.args.cuda:
            x = x.cuda()
            model = model.cuda()

            if risk_factor_vector is not None:
                risk_factors = risk_factors.cuda()

            logger.debug("Inference with GPU")
        else:
            model = model.cpu()
            logger.debug("Inference with CPU")

        ## Index 0 to toss batch dimension
        pred_y = F.softmax(model(x, risk_factors)[0])[0]
        pred_y = np.array(self.label_map(pred_y.cpu().data.numpy()))

        logger.info("Pred: {}".format(pred_y))

        return pred_y

    def run_model(self, dicom_files, payload=None):
        if payload is None:
            payload = {
                'dcmtk': True
            }
        elif 'dcmtk' not in payload:
            payload['dcmtk'] = True

        if payload['dcmtk']:
            logger.info('Using dcmtk')
        else:
            logger.info('Using pydicom')

        model = self.load_model()

        preds = []

        for dicom in dicom_files:
            dicom_path = tempfile.NamedTemporaryFile(suffix='.dcm').name
            image_path = tempfile.NamedTemporaryFile(suffix='.png').name

            dicom.seek(0)
            dicom.save(dicom_path)

            if payload['dcmtk']:
                image = dicom_to_image_dcmtk(dicom_path, image_path)
                logger.debug('Image mode: {}'.format(image.mode))
            else:
                dicom = pydicom.dcmread(dicom_path)
                image = dicom_to_arr(dicom, pillow=True)

            risk_factor_vector = None
            preds.append(self.process_image(image, model, risk_factor_vector))

        counts = np.bincount(preds)
        y = np.argmax(counts)

        if isinstance(y, np.generic):
            y = y.item()

        report = {'predictions': y}

        return report
