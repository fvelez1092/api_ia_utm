from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.utils.response import create_response
from app.services import auth_service
from app.schemas.auth_schema import AuthSchema

auth_blueprint = Blueprint("Auth", __name__, url_prefix="/auth")
"""Entidad - Autenticación"""


@auth_blueprint.route("/login", methods=["POST"])
def login():
    json_data = request.get_json(force=True)
    json_data = AuthSchema().load(json_data)
    auth_data = auth_service.login(json_data["username"], json_data["password"])
    if auth_data is None:
        return create_response(
            "error",
            data={"message": "Usuario o contraseña incorrectos"},
            status_code=401,
        )
    return create_response("success", data={"auth": auth_data}, status_code=200)


@auth_blueprint.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    if auth_service.logout(jti):
        return create_response("success", data={"message": "Logout"}, status_code=200)
    else:
        return create_response("error", data={"message": "Logout"}, status_code=500)
