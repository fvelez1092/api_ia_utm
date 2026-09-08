"""Decoradores de autorización."""

from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.utils.response import create_response


def admin_required():
    def wrapper(function):
        @wraps(function)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            if get_jwt().get("role") != "admin":
                return create_response(
                    "error",
                    message="Se requieren permisos de administrador.",
                    status_code=403,
                )
            return function(*args, **kwargs)

        return decorated

    return wrapper
