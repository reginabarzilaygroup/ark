import logging

from models.base import BaseModel
from onconet.models.mirai_full import MiraiModel


class MiraiModelWrapper(BaseModel):
    def __init__(self, args):
        super().__init__()
        self.model = MiraiModel(args)
        self.__version__ = self.model.__version__

    def run_model(self, dicom_files, payload=None):

        logger = logging.getLogger('ark')
        logger.info(f"Beginning inference version {self.model.__version__}")
        scores = self.model.run_model(dicom_files, payload=payload)
        report = {'predictions': scores}

        return report
