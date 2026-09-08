"""Extensiones compartidas de Flask."""

import logging

from flask import has_request_context, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt_instance = Bcrypt()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.base_url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None
        return super().format(record)


logger_app = logging.getLogger("api_ia_utm")
if not logger_app.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        RequestFormatter(
            "[%(asctime)s] %(remote_addr)s %(url)s %(levelname)s: %(message)s"
        )
    )
    logger_app.addHandler(handler)
logger_app.setLevel(logging.INFO)
