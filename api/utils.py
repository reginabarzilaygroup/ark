import os
import requests
import zipfile

import pydicom
from requests_file import FileAdapter
from werkzeug.datastructures import FileStorage


def validate_post_request(req, required=None, max_size=8 * 10**8):
    """Validates the DICOM POST JSON payload.

    Args:
        req (flask.Request): Flask request object
        required (list): List of keys required to be in the request JSON; default is None
        max_size (int): Maximum size of the request body in bytes; default is 8*10^8

    Returns:
        None
    """
    if req.form and req.content_length > max_size:
        raise RuntimeError("Request data too large: {} > {}".format(req.content_length, max_size))

    if required is not None:
        if 'data' in req.form:
            data = req.form['data']
            invalid = []

            for item in required:
                if item not in data:
                    invalid.append(item)

            if invalid:
                raise RuntimeError("Missing keys in request JSON: {}".format(invalid))
        else:
            raise RuntimeError("'data' not in request JSON; {}".format(req.form.keys()))

    if 'dicom' not in req.files:
        raise RuntimeError("Request does not contain `dicom` array")


def download_zip(uri, path='/tmp/', local_file=False):
    zip_path = path + 'dicom.zip'
    dir_path = path + 'dicom/'

    # TODO: deactivate for prod
    s = requests.Session()
    s.mount('file://', FileAdapter())
    results = s.get(uri)

    with open(zip_path, 'wb') as f:
        f.write(results.content)

    with zipfile.ZipFile(zip_path) as f:
        f.extractall(path=dir_path)

    os.remove(zip_path)


def dicom_dir_walk(path='/tmp'):
    dir_path = path + '/dicom'

    dicom_files = []

    for root, dirs, files in os.walk(dir_path):
        if 'DICOMDIR' in files:
            ds = pydicom.dcmread(os.path.join(root, 'DICOMDIR'))

            for instance in ds.DirectoryRecordSequence:
                if instance[0x0004, 0x1430].value == 'IMAGE':
                    ref = instance[0x0004, 0x1500].value
                    file_path = os.path.join(root, '/'.join(ref))

                    f = open(file_path, 'rb')
                    # TODO: change file IO
                    dicom_files.append(FileStorage(f))

                    break

    return dicom_files
