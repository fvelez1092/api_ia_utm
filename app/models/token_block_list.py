from app.extensions import db
from app.models.declarative_base import DeclarativeBase
from app.utils.utilities import timeNowTZ


class TokenBlockList(DeclarativeBase):
    __tablename__ = "token_block_list"
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(200), nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=timeNowTZ)

    def __init__(self, jti):
        self.jti = jti
