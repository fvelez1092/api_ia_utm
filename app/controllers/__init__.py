"""Blueprints HTTP de la aplicación."""

from app.controllers.auth_controller import auth_blueprint
from app.controllers.document_controller import document_blueprint
from app.controllers.rag_controller import rag_blueprint
from app.controllers.user_controller import user_blueprint


BLUEPRINTS = (
    auth_blueprint,
    user_blueprint,
    document_blueprint,
    rag_blueprint,
)

__blueprints__ = BLUEPRINTS
