from datetime import datetime, timedelta

from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.mongo_base_model import MongoDAO
from config import DATETIME_FMT, TZ, TELEMETRY_INTERVAL


class TelemetryTrnSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    logtime = fields.DateTime(format=DATETIME_FMT)
    server_id = fields.String(required=False)

    net_recv = fields.Integer(required=False)
    net_send = fields.Integer(required=False)
    req_total = fields.Integer(required=False)
    latency= fields.Float(required=False)


class TelemetryTrnDao(MongoDAO):
    def __init__(self):
        super().__init__("telemetry", schema=TelemetryTrnSchema)


    def get_by_logtime(self, dt_start):
        query = [
            {
                "$match": {
                    "logtime": {
                        "$gte": dt_start
                    }
                }
            },
            {
                "$group": {
                    "_id": "null",
                    "net_recv": {"$sum": "$net_recv"},
                    "net_send": {"$sum": "$net_send"},
                    "req_total":{"$sum": "$req_total"},
                    "latency": {"$avg": "$latency"}
                }
            }
        ]
        logger.debug(query)
        rs = self.collection.aggregate(query)
        return list(rs)