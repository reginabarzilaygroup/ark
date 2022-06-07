from version import __version__ as ark_version


class BaseModel:
    def __init__(self):
        self.__version__ = None
        self.required_data = None

    def run_model(self, dicom_file, payload=None):
        raise NotImplementedError("run_model function not implemented")


class EmptyModel(BaseModel):
    def __init__(self, args):
        super().__init__()
        self.__version__ = ark_version

    def run_model(self, dicom_file, payload=None):
        return


class ArgsDict(object):
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)
