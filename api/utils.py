from collections import Iterable
from pathlib import Path


def validate_post_json(req, required=None, max_size=8 * 10**6):
    """Validates the DICOM POST JSON payload.

    Args:
        req (flask.Request): Flask request object
        required (list): List of keys required to be in the request JSON; default is None
        max_size (int): Maximum size of the request body in bytes; default is 8*10^6

    Returns:
        None
    """
    if required is None:
        required = []

    if req.content_length > max_size:
        raise RuntimeError("POST data too large: {} > {}".format(req.content_length, max_size))
    elif req.is_json:
        data = req.get_json()
        invalid = []

        for item in required:
            if item not in data:
                invalid.append(item)

        if invalid:
            raise RuntimeError("Invalid/missing keys in JSON: {}".format(invalid))
    else:
        raise RuntimeError("POST data not JSON: {}".format(req.get_data()))


def validate_list_paths(fp):
    """Validates the DICOM POST file path.

    Args:
        fp (Union[str, Path, Iterable]): A directory path or list of file paths

    Returns:
        list: List of file paths
    """
    if isinstance(fp, str) or isinstance(fp, Path):
        fps = Path(fp)

        if fps.is_dir():
            fps = list(fps.iterdir())
        else:
            raise NotADirectoryError("Not a valid directory: {}".format(fps))
    elif isinstance(fp, Iterable):
        fps = [Path(f) for f in fp]
    else:
        raise RuntimeError("Input is not a valid directory path or list of file paths: {}".format(fp))

    return fps
