from marshmallow import fields, validate
from app.schemas.base_schema import BaseSchema


class AuthSchema(BaseSchema):
    username = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    password = fields.Str(required=True)
