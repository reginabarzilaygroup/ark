import datetime
import functools
import json
import os
import pprint
import threading
import uuid

import requests


def get_info_dict(app):
    info_dict = {
        'apiVersion': app.config['API_VERSION'],
        'modelName': app.config['MODEL_NAME'],
        'modelVersion': app.config['MODEL'].__version__,
    }
    return info_dict


def cache_on_success(func):
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a unique key based on function arguments
        key = (args, tuple(sorted(kwargs.items())))

        # If the function call with these arguments is already cached, return the cached value
        if key in cache:
            return cache[key]

        try:
            result = func(*args, **kwargs)
            # Cache the result if the function completes successfully
            cache[key] = result
            return result
        except Exception:
            # Return None and do not cache anything if an exception occurs
            return None

    return wrapper


@cache_on_success
def get_mac_address():
    mac = uuid.getnode()
    mac_string = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    return mac_string


@cache_on_success
def get_ip_address():
    return requests.get("http://ident.me", timeout=60).content.decode("utf-8")


def log_analytics(app, data=None):

    analytics_url = os.environ.get("ARK_ANALYTICS_URL", None)
    analytics_api_key = os.environ.get("ARK_ANALYTICS_API_KEY", None)
    do_log = os.environ.get("ARK_LOG_ANALYTICS", "false").lower() == "true"
    if not do_log or not analytics_url or not analytics_api_key:
        return

    log_data = get_info_dict(app)
    if data:
        log_data.update(data)

    copy_keys = ["ARK_USERNAME", "ARK_HOSTNAME", "ARK_SITENAME"]
    for ck in copy_keys:
        if ck in os.environ:
            log_data[ck] = os.environ[ck]

    try:
        utc_now = datetime.datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=datetime.timezone.utc)
        log_data["TIMESTAMP"] = utc_now.strftime("%Y-%m-%d %H:%M:%S %Z%z")

        log_data["IP"] = get_ip_address()
        log_data["MAC"] = get_mac_address()

        headers = {
            'content-type': "application/json",
            'x-apikey': analytics_api_key,
            'cache-control': "no-cache"
        }
        payload = json.dumps(log_data)
        response = requests.request("POST", analytics_url, data=payload, headers=headers)
        # response_json = json.loads(response.text)
        # print(f"Response:\n{pprint.pformat(response_json)}")
    except Exception as e:
        # Handle or log the exception, but don't raise it to avoid affecting the main response
        print(f"Analytics logging failed: {e}")


def async_log_analytics(app, data):
    thread = threading.Thread(target=log_analytics, args=(app,), kwargs={"data": data})
    thread.start()
