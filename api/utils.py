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
