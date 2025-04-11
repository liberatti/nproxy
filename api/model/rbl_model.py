from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.feed_model import FeedSchema
from api.model.mongo_base_model import MongoDAO
from api.tools.network_tool import NetworkTool


class RBLSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    net_start = fields.String()
    net_end = fields.String()
    network = fields.String()
    version = fields.Integer()
    src_type = fields.String()  # feed, pass_list, jail
    src_type_id = fields.String()  # _id from source


class RBLDao(MongoDAO):
    def __init__(self):
        super().__init__("rbl", schema=FeedSchema)

    def check_by_ip(self, ip, sensor):
        ip_id = NetworkTool.id(ip)

        bl_providers = []
        if "block" in sensor:
            for sb in sensor["block"]:
                if sb:
                    bl_providers.append(ObjectId(sb["_id"]))

        if "jails" in sensor:
            for sb in sensor["jails"]:
                if sb:
                    bl_providers.append(ObjectId(sb["_id"]))

        per_providers = []
        if "permit" in sensor:
            for sb in sensor["permit"]:
                if sb:
                    per_providers.append(ObjectId(sb["_id"]))

        query = [
            {
                "$match": {
                    "net_start": {"$lte": ip_id},
                    "net_end": {"$gte": ip_id},
                    "version": {"$eq": 4 if NetworkTool.is_ipv4(ip) else 6},
                }
            },
            {
                "$facet": {
                    "pass": [
                        {
                            "$match": {
                                "action": "pass",
                                "provider_id": {"$in": per_providers},
                            }
                        }
                    ],
                    "deny": [
                        {
                            "$match": {
                                "action": "deny",
                                "provider_id": {"$in": list(set(bl_providers))},
                            }
                        }
                    ],
                }
            },
            {
                "$project": {
                    "result": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$pass"}, 0]},
                            "then": [],
                            "else": "$deny",
                        }
                    }
                }
            },
            {"$unwind": "$result"},
            {"$replaceRoot": {"newRoot": "$result"}},
        ]
        logger.debug(query)
        rs = list(self.collection.aggregate(query))
        return {"blocked": (len(rs) > 0)}

    def delete_by_provider(self, provider_type, provider_id):
        query = {
            "$and": [
                {"provider_type": {"$eq": provider_type}},
                {"provider_id": {"$eq": ObjectId(provider_id)}},
            ]
        }
        self.collection.delete_many(query)

    def delete_expired(self, provider_type, provider_id, bantime_limit):
        query = {
            "$and": [
                {"provider_type": {"$eq": provider_type}},
                {"provider_id": {"$eq": ObjectId(provider_id)}},
                {"banned_on": {"$lte": bantime_limit}},
            ]
        }
        logger.debug(query)
        self.collection.delete_many(query)
