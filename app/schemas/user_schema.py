from marshmallow import fields, validate
from app.schemas.base_schema import BaseSchema


class UserSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    role = fields.Str(
        validate=validate.OneOf(["admin", "user"])
    )

    status = fields.Bool(dump_only=True)
    creation_date = fields.DateTime(format="%d/%m/%Y %H:%M:%S", dump_only=True)
