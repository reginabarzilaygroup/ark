import io
import logging

from models.base import BaseModel
from onconet.models.mirai_full import MiraiModel


class MiraiModelWrapper(BaseModel):
    def __init__(self, args):
        super().__init__()
        self.model = MiraiModel(args)
        self.__version__ = self.model.__version__

    def run_model(self, dicom_files, payload=None, to_dict=False, return_attentions=False):

        logger = logging.getLogger('ark')
        logger.info(f"Beginning inference version {self.model.__version__}")
        if isinstance(dicom_files[0], bytes):
            dicom_files = [io.BytesIO(dicom_file) for dicom_file in dicom_files]
        for ff in dicom_files:
            ff.seek(0)
        report = self.model.run_model(dicom_files, payload=payload)

        return report
