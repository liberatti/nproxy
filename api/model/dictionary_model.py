from marshmallow import EXCLUDE, Schema, fields

from api.model.mongo_base_model import MongoDAO


class DataObjectSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    slug = fields.String()
    type = fields.String()  # network
    scope = fields.String()  # system, user
    content = fields.List(fields.String())
    usage = fields.Integer()
    description = fields.String()


class DictionaryDao(MongoDAO):
    def __init__(self):
        super().__init__("dictionary", schema=DataObjectSchema)

    def get_by_slug(self, slug):
        rs = self.collection.find_one({"slug": slug})
        self._load(rs)
        return rs
