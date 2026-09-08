from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from app.schemas.user_schema import UserSchema
from app.services import user_service
from app.utils.auth import admin_required
from app.utils.response import create_response


user_blueprint = Blueprint("User", __name__, url_prefix="/user")


@user_blueprint.get("/")
@admin_required()
def get_all():
    return create_response(
        "success", data={"users": user_service.get_all()}, status_code=200
    )


@user_blueprint.get("/<int:user_id>")
@admin_required()
def get(user_id: int):
    user = user_service.get(user_id)
    if user is None:
        return create_response("error", message="Usuario no encontrado.", status_code=404)
    return create_response("success", data={"user": user}, status_code=200)


@user_blueprint.post("/")
@admin_required()
def create():
    if not request.is_json:
        return create_response("error", message="Se requiere JSON.", status_code=415)
    data = UserSchema().load(request.get_json(silent=True) or {})
    user, reason = user_service.create(
        data["username"], data["password"], data.get("role", "user")
    )
    if user is None:
        return create_response("error", message=reason, status_code=409)
    return create_response("success", data={"user": user}, status_code=201)


@user_blueprint.put("/<int:user_id>")
@admin_required()
def update(user_id: int):
    if not request.is_json:
        return create_response("error", message="Se requiere JSON.", status_code=415)
    data = UserSchema().load(request.get_json(silent=True) or {})
    current_user = user_service.get(user_id)
    if current_user is None:
        return create_response("error", message="Usuario no encontrado.", status_code=404)
    user, reason = user_service.update(
        user_id,
        data["username"],
        data["password"],
        data.get("role", current_user["role"]),
    )
    if user is None:
        status = 409 if "existe" in reason else 404
        return create_response("error", message=reason, status_code=status)
    return create_response("success", data={"user": user}, status_code=200)


@user_blueprint.delete("/<int:user_id>")
@admin_required()
def delete(user_id: int):
    if str(user_id) == get_jwt_identity():
        return create_response(
            "error",
            message="No puede eliminar su propia cuenta administrativa.",
            status_code=400,
        )
    deleted, message = user_service.delete(user_id)
    if not deleted:
        return create_response("error", message=message, status_code=404)
    return create_response("success", data={"message": message}, status_code=200)
