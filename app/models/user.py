from app.extensions import db
from app.utils.utilities import timeNowTZ


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    status = db.Column(db.Boolean, nullable=False, default=True)
    creation_date = db.Column(db.DateTime, nullable=True, default=timeNowTZ)

    def __init__(self, username, password, role="user"):
        self.username = username
        self.password = password
        self.role = role
