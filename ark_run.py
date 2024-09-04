#!/usr/bin/env python

import os
import platform
import subprocess
import sys

import api.config
from api.config import PROJECT_DIR


def _check_help():
    if len(sys.argv) > 1 and sys.argv[1] in {"help", "--help", "-h"}:
        return True
    return False


def cli_entrypoint(model_name="auto"):
    cli_help = \
        """
        Convenience tool to launch flask server using gunicorn.

        In the simplest case, you can simply run:
        $ ark-run

        This will automatically detect the model in the current environment and launch the server.
        The model must be installed in the current environment; this can be done simply with:

        $ pip install 'ark[mirai]'

        or 

        $ pip install 'ark[sybil]'

        It is not recommended to install both models in the same environment, 
        as they have slightly different dependencies.


        If you'd like to specify a model, you can run:
        $ ark-run <model_name>

        where <model_name> is one of "empty", "mirai", or "sybil".

        $ ark-run empty

        will launch the server with an empty model, which is useful for testing the API.
        """

    if _check_help():
        print(cli_help)
        exit(0)

    if len(sys.argv) > 1:
        model_name = sys.argv[1]

    api.config.set_config_by_name(model_name)

    LOGLEVEL_KEY = "LOG_LEVEL"
    loglevel = os.environ.get(LOGLEVEL_KEY, "INFO")
    threads = os.environ.get("ARK_THREADS", "4")
    if platform.system() == "Windows":
        args = ["waitress-serve",
                "--channel-timeout", "3600",
                "--threads", threads,
                "--port", "5000",
                "--call", "main:create_app"]

    else:
        args = ["gunicorn",
                "--bind", "0.0.0.0:5000",
                "--timeout", "0",
                "--threads", threads,
                "--log-level", loglevel,
                "--access-logfile", "-",
                "main:create_app()"]

    proc = subprocess.run(args, stdout=None, stderr=None, text=True, cwd=PROJECT_DIR)


def cli_entrypoint_empty():
    cli_entrypoint("empty")


def cli_entrypoint_mirai():
    import onconet
    cli_entrypoint("mirai")


def cli_entrypoint_sybil():
    import sybil
    cli_entrypoint("sybil")
