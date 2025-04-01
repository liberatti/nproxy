from marshmallow import EXCLUDE, Schema, fields

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
        for sb in sensor["block"]:
            bl_providers.append(sb["_id"])
        per_providers = []
        for sb in sensor["permit"]:
            per_providers.append(sb["_id"])

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
                                "provider_id": {"$in": bl_providers},
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
        rs = list(self.collection.aggregate(query))
        return {"blocked": (len(rs) > 0)}

    def delete_by_provider(self, provider_type, provider_id):
        query = {
            "$and": [
                {"provider_type": {"$eq": provider_type}},
                {"provider_id": {"$eq": provider_id}},
            ]
        }
        self.collection.delete_many(query)
