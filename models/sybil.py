import logging
import tempfile
import os

from models.base import BaseModel
from sybil import Serie, Sybil
from sybil import __version__ as sybil_version

logger = logging.getLogger('ark')


class Args(object):
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)


class SybilModel(BaseModel):
    def __init__(self, args):
        super().__init__()
        self.__version__ = sybil_version
        self.model = Sybil(name_or_path='sybil_ensemble')

    def run_model(self, dicom_files, payload=None, to_dict=False):
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
        threads = int(os.getenv("SYBIL_THREADS", 0))
        scores = self.model.predict([serie], threads=threads)

        for dicom_path in dicom_paths:
            try:
                os.unlink(dicom_path)
            except Exception as e:
                pass

        if to_dict:
            scores = scores.scores[0]
            scores = {f"Year {idx + 1}": result for idx, result in enumerate(scores)}
        report = {"predictions": scores}

        return report
