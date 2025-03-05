from datetime import datetime, timedelta

from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.mongo_base_model import MongoDAO
from config import DATETIME_FMT, TZ


class TelemetryTrnSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    logtime = fields.DateTime(format=DATETIME_FMT)
    service_id = fields.String(required=False)
    server_id = fields.String(required=False)

    net_recv = fields.Integer(required=False)
    net_send = fields.Integer(required=False)
    req_total = fields.Integer(required=False)


class TelemetryTrnDao(MongoDAO):
    def __init__(self):
        super().__init__("telemetry", schema=TelemetryTrnSchema)

    def get_node_bandwidth(self,server_id):
        query= [
            {
                "$match": {
                    "logtime": {
                        "$gte": (datetime.now(TZ) - timedelta(minutes=5))
                    },
                    "server_id": server_id
                },
            },
            {"$sort": {"logtime": -1}},
            {"$limit": 1}
        ]
        logger.debug(query)
        rs = self.collection.aggregate(query)
        return list(rs)

    def get_offset(self):
        query= [
            { "$sort": { "logtime": -1 } },
            { "$limit": 1 }
        ]
        logger.debug(query)
        rs=list(self.collection.aggregate(query))
        if rs:
            return rs[0]['logtime']
        else:
            return datetime.now(TZ) - timedelta(days=1)