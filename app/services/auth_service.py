from app.extensions import db, bcrypt_instance
from app.models.user import User
from app.models.token_block_list import TokenBlockList
from flask_jwt_extended import create_access_token  # , create_refresh_token


def login(username: str, password: str):
    user_object = (
        db.session.query(User)
        .filter(User.username == username, User.status == True)
        .first()
    )
    if user_object is not None:
        if bcrypt_instance.check_password_hash(user_object.password, password):
            user_identity = {"id": user_object.id, "username": user_object.username}
            access_token = create_access_token(identity=user_identity)
            # refresh_token = create_refresh_token(identity=user_identity)
            return {"access_token": access_token}
        else:
            return None
    else:
        return None


def logout(jti: str):
    token_block_list = TokenBlockList(jti)
    db.session.add(token_block_list)
    db.session.commit()
    return True
