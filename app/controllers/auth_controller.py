from flask import Blueprint, request
from flask_jwt_extended import get_jwt, jwt_required

from app.schemas.auth_schema import AuthSchema
from app.extensions import limiter
from app.services import auth_service
from app.utils.response import create_response


auth_blueprint = Blueprint("Auth", __name__, url_prefix="/auth")


@auth_blueprint.post("/login")
@limiter.limit("10 per minute")
def login():
    if not request.is_json:
        return create_response(
            "error", message="Se requiere JSON.", status_code=415
        )
    credentials = AuthSchema().load(request.get_json(silent=True) or {})
    auth_data = auth_service.login(credentials["username"], credentials["password"])
    if auth_data is None:
        return create_response(
            "error", message="Usuario o contraseña incorrectos.", status_code=401
        )
    return create_response("success", data={"auth": auth_data}, status_code=200)


@auth_blueprint.delete("/logout")
@jwt_required()
def logout():
    auth_service.logout(get_jwt()["jti"])
    return create_response(
        "success", data={"message": "Sesión cerrada."}, status_code=200
    )
