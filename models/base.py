class BaseModel:
    def __init__(self):
        self.required_data = None

    def run_model(self, dicom_file, payload=None):
        raise NotImplementedError("run_model function not implemented")


class EmptyModel(BaseModel):
    def __init__(self):
        super().__init__()

    def run_model(self, dicom_file, payload=None):
        return
