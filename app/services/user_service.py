from app.extensions import db, bcrypt_instance
from app.models.user import User
from app.schemas.user_schema import UserSchema


def exists(username: str):
    user_object = (
        db.session.query(User)
        .filter(User.username == username, User.status == True)
        .first()
    )
    if user_object is not None:
        return True
    else:
        return False


def get(id: int):
    user_object = (
        db.session.query(User).filter(User.id == id, User.status == True).first()
    )
    user_dict = UserSchema(exclude=("password",)).dump(user_object)
    return user_dict


def get_all():
    user_objects = db.session.query(User).filter(User.status == True).all()
    user_list = UserSchema(exclude=("password",), many=True).dump(user_objects)
    return user_list


def create(username: str, password: str):
    if exists(username):
        return None
    # password_hash = bcrypt_instance.hashpw(password.encode('utf8'), bcrypt_instance.gensalt())
    # user_object = User(username, password_hash.decode('utf8'))
    user_object = User(
        username, bcrypt_instance.generate_password_hash(password).decode("utf8")
    )
    db.session.add(user_object)
    db.session.commit()
    user_dict = UserSchema(exclude=("password",)).dump(user_object)
    return user_dict


def update(id: int, username: str, password: str):
    user_object = (
        db.session.query(User).filter(User.id == id, User.status == True).first()
    )
    user_object.username = username
    user_object.password = bcrypt_instance.generate_password_hash(password).decode(
        "utf8"
    )
    db.session.commit()
    user_dict = UserSchema(exclude=("password",)).dump(user_object)
    return user_dict


def delete(id: int):
    user_object = (
        db.session.query(User).filter(User.id == id, User.status == True).first()
    )
    if user_object is None:
        return (False, "Usuario no encontrado")
    user_object.status = False
    db.session.commit()
    return (True, "Usuario eliminado")
