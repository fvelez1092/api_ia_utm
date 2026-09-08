"""Operaciones de usuarios."""

from sqlalchemy.exc import IntegrityError

from app.extensions import bcrypt_instance, db
from app.models.user import User
from app.schemas.user_schema import UserSchema


def get(user_id: int):
    user = db.session.query(User).filter_by(id=user_id, status=True).first()
    return UserSchema().dump(user) if user else None


def get_all():
    users = db.session.query(User).filter_by(status=True).order_by(User.id).all()
    return UserSchema(many=True).dump(users)


def create(username: str, password: str, role: str = "user"):
    if db.session.query(User.id).filter_by(username=username).first():
        return None, "El nombre de usuario ya existe."

    user = User(
        username=username,
        password=bcrypt_instance.generate_password_hash(password).decode("utf-8"),
        role=role,
    )
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "El nombre de usuario ya existe."
    return UserSchema().dump(user), None


def update(user_id: int, username: str, password: str, role: str):
    user = db.session.query(User).filter_by(id=user_id, status=True).first()
    if user is None:
        return None, "Usuario no encontrado."

    duplicate = db.session.query(User.id).filter(
        User.username == username, User.id != user_id
    ).first()
    if duplicate:
        return None, "El nombre de usuario ya existe."

    user.username = username
    user.password = bcrypt_instance.generate_password_hash(password).decode("utf-8")
    user.role = role
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "El nombre de usuario ya existe."
    return UserSchema().dump(user), None


def delete(user_id: int):
    user = db.session.query(User).filter_by(id=user_id, status=True).first()
    if user is None:
        return False, "Usuario no encontrado."
    user.status = False
    db.session.commit()
    return True, "Usuario eliminado."
