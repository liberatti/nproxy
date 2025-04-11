from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.mongo_base_model import MongoDAO


class OIDCToken(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(default="Bearer")
    expires_in = fields.Integer()
    provider = fields.String()


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    email = fields.String()
    password = fields.String()
    locale = fields.String(required=False)
    role = fields.String()


class UserDao(MongoDAO):
    def __init__(self):
        super().__init__("users", schema=UserSchema)

    def get_by_email(self, email):
        query={"email": email}
        logger.debug(query)
        v = self.collection.find_one(query)
        super()._load(v)
        return v
