from marshmallow import EXCLUDE, Schema, fields

from api.model.feed_model import FeedSchema
from api.model.mongo_base_model import MongoDAO


class RBLSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    range_start = fields.String()
    range_end = fields.String()
    network = fields.String()
    version = fields.Integer()
    src_type = fields.String()  # feed, pass_list, jail
    src_type_id = fields.String()  # _id from source


class RBLDao(MongoDAO):
    def __init__(self):
        super().__init__("rbl", schema=FeedSchema)

    def check_by_ip(self, ip, provider_ids):
        query = {
            "$and": [
                {"range_start": {"$lte": ip}},
                {"range_end": {"$gte": ip}},
                {"provider_id": {"$in": provider_ids}},
            ]
        }
        rs = list(self.collection.find(query))
        for i in rs:
            self._load(i)
        return rs

    def delete_by_provider(self, provider_type, provider_id):
        query = {
            "$and": [
                {"provider_type": {"$eq": provider_type}},
                {"provider_id": {"$eq": provider_id}},
            ]
        }
        self.collection.delete_many(query)
