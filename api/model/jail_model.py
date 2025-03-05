from datetime import datetime

from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import replace_tz
from api.model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class JailEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    ipaddr = fields.String()
    banned_on = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)


class JailSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    bantime = fields.Integer()
    content = fields.Nested(JailEntrySchema, many=True)


class JailDao(MongoDAO):
    def __init__(self):
        super().__init__("jail", schema=JailSchema)

    def persist(self, vo):
        default_date = (
            replace_tz(datetime.now()).replace(microsecond=0)
        )

        for c in vo["content"]:
            if "banned_on" not in c:
                c.update({"banned_on": default_date})
        return super().persist(vo)
