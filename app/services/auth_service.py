"""Operaciones de autenticación."""

from flask_jwt_extended import create_access_token

from app.extensions import bcrypt_instance, db
from app.models.token_block_list import TokenBlockList
from app.models.user import User


def login(username: str, password: str):
    user = db.session.query(User).filter_by(username=username, status=True).first()
    if user is None or not bcrypt_instance.check_password_hash(user.password, password):
        return None

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username, "role": user.role},
    )
    return {"access_token": access_token, "role": user.role}


def logout(jti: str):
    if not db.session.query(TokenBlockList.id).filter_by(jti=jti).first():
        db.session.add(TokenBlockList(jti))
        db.session.commit()
    return True
