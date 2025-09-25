from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.utils.response import create_response
from app.services import user_service
from app.schemas.user_schema import UserSchema

user_blueprint = Blueprint("User", __name__, url_prefix="/user")
"""Entidad - Usuario"""


@user_blueprint.route("/", methods=["GET"])
@jwt_required()
def get_all():
    users = user_service.get_all()
    return create_response("success", data={"users": users}, status_code=200)


@user_blueprint.route("/<int:id>", methods=["GET"])
@jwt_required()
def get(id: int):
    user = user_service.get(id)
    return create_response("success", data={"user": user}, status_code=200)


@user_blueprint.route("/", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json(force=True)
    json_data = UserSchema().load(json_data)
    user = user_service.create(json_data["username"], json_data["password"])
    if user is None:
        return create_response(
            "error", data={"message": "Usuario ya existe"}, status_code=409
        )
    return create_response("success", data={"user": user}, status_code=201)


@user_blueprint.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update(id: int):
    json_data = request.get_json(force=True)
    json_data = UserSchema().load(json_data)
    user = user_service.update(id, json_data["username"], json_data["password"])
    return create_response("success", data={"user": user}, status_code=200)


@user_blueprint.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete(id: int):
    user_delete = user_service.delete(id)
    if user_delete[0]:
        return create_response(
            "success", data={"message": user_delete[1]}, status_code=200
        )
    else:
        return create_response(
            "error", data={"message": user_delete[1]}, status_code=404
        )
