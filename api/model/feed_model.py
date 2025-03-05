from marshmallow import EXCLUDE, Schema, fields

from api.model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class FeedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    slug = fields.String()
    provider = fields.String()
    version = fields.String()
    type = fields.String()  # network, ruleset
    scope = fields.String()  # system, user
    source = fields.String()
    description = fields.String()
    update_interval = fields.String()
    updated_on = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)


class FeedDao(MongoDAO):
    def __init__(self):
        super().__init__("feeds", schema=FeedSchema)

    def get_by_slug(self, slug):
        rs = self.collection.find_one({"slug": slug})
        self._load(rs)
        return rs

    def get_by_type(self, _type):
        rows = list(self.collection.find({"type": {"$regex": f".*{_type}.*"}}))
        for e in rows:
            self._load(e)
        return rows
