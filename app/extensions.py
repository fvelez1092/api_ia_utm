"""Extensiones de la aplicación."""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import logging
from flask import has_request_context, request

db = SQLAlchemy()
"""Instancia de SQLAlchemy"""

bcrypt_instance = Bcrypt()
"""Instancia de Bcrypt"""

jwt = JWTManager()
"""Instancia de JWTManager"""


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


handler = logging.FileHandler("app.log")
handler.setLevel(logging.NOTSET)
formatter = RequestFormatter(
    "[%(asctime)s] %(remote_addr)s requested %(url)s\n%(levelname)s in %(module)s: %(message)s"
)
handler.setFormatter(formatter)

logger_app = logging.getLogger(__name__)
"""Logger Object for the application."""

logger_app.addHandler(handler)
