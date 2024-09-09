import logging
import tempfile
import os

import numpy as np

from models.base import BaseModel
from sybil import Serie, Sybil, collate_attentions
from sybil import __version__ as sybil_version

logger = logging.getLogger('ark')


class Args(object):
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)


class SybilModel(BaseModel):
    def __init__(self, args):
        super().__init__()
        self.__version__ = sybil_version
        name_or_path = os.getenv("ARK_SYBIL_MODEL_NAME", 'sybil_ensemble')
        self.model = Sybil(name_or_path=name_or_path)

    def run_model(self, dicom_files, payload=None, to_dict=False, return_attentions=False):
        dicom_paths = []

        for dicom in dicom_files:
            try:
                dicom_file = tempfile.NamedTemporaryFile(suffix='.dcm', delete=False)
                dicom_path = dicom_file.name

                if hasattr(dicom, 'save'):
                    dicom.save(dicom_path)
                else:
                    dicom_file.write(dicom)
                    dicom_file.flush()

                dicom_paths.append(dicom_path)
            except Exception as e:
                logger.warning("{}: {}".format(type(e).__name__, e))

        serie = Serie(dicom_paths)
        N = len(dicom_paths)
        threads = int(os.getenv("SYBIL_THREADS", 0))
        predictions = self.model.predict([serie], threads=threads, return_attentions=return_attentions)

        for dicom_path in dicom_paths:
            try:
                os.unlink(dicom_path)
            except Exception as e:
                pass

        if to_dict:
            scores = predictions.scores[0]
            scores = {f"Year {idx + 1}": result for idx, result in enumerate(scores)}
            predictions = [scores, predictions[1]]

        if return_attentions:
            predictions = list(predictions)
            attention_up = collate_attentions(predictions[1][0], N, eps=1e-4)
            attention_up = attention_up.squeeze()
            predictions[1] = array_to_list_nested(attention_up)

        report = {"predictions": predictions}

        return report

def array_to_list_nested(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: array_to_list_nested(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [array_to_list_nested(v) for v in obj]
    return obj
