"""Conversión centralizada de excepciones a respuestas HTTP."""

from flask import current_app
from marshmallow.exceptions import ValidationError
from werkzeug.exceptions import HTTPException

from app.extensions import db, logger_app
from app.utils.response import create_response


def handle_error(error):
    try:
        db.session.rollback()
    except Exception:
        pass

    if isinstance(error, ValidationError):
        return create_response(
            "fail",
            data=error.messages,
            message="Datos de entrada inválidos.",
            status_code=422,
        )

    if isinstance(error, HTTPException):
        return create_response(
            "error", message=error.description, status_code=error.code or 500
        )

    logger_app.exception("Error no controlado", exc_info=error)
    data = {"detail": str(error)} if current_app.debug else None
    return create_response(
        "error",
        data=data,
        message="Error interno del servidor.",
        status_code=500,
    )
