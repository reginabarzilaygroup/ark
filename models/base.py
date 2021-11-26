class BaseModel:
    def __init__(self, args):
        self.args = args

    def run_model(self, dicom_file, payload=None):
        raise NotImplementedError("run_model function not implemented")
