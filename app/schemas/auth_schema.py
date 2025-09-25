from marshmallow import fields
from app.schemas.base_schema import BaseSchema


class AuthSchema(BaseSchema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
