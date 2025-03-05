from datetime import datetime

from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.mongo_base_model import MongoDAO
from api.model.sensor_model import SensorSchema, SensorDao
from api.model.service_model import ServiceSchema, ServiceDao
from api.model.upstream_model import UpstreamSchema, UpstreamDao
from config import DATETIME_FMT, TZ


class TransactionHeaderSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=False)
    content = fields.String(required=False)


class TransactionRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    method = fields.String(required=False)
    uri = fields.String(required=False)
    bytes = fields.Integer(required=False)
    headers = fields.Nested("TransactionHeaderSchema", many=True, allow_none=True)


class TransactionResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    status_code = fields.Integer(required=False)
    bytes = fields.Integer(required=False)
    headers = fields.Nested("TransactionHeaderSchema", many=True, allow_none=True)


class TransactionUserAgentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    family = fields.String(required=False)
    major = fields.String(required=False)
    minor = fields.String(required=False)


class TransactionGeoSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    addr = fields.String(required=False)
    range_start = fields.String(required=False)
    range_end = fields.String(required=False)
    ans_number = fields.String(required=False)
    organization = fields.String(required=False)
    country = fields.String(required=False)


class TransactionSourceSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    ip = fields.String(required=False)
    port = fields.String(required=False)
    geo = fields.Nested(TransactionGeoSchema)


class TransactionDestinationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    ip = fields.String(required=False)
    port = fields.String(required=False)


class TransactionHttpSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    duration = fields.Decimal(required=False)
    request_line = fields.String(required=False)
    version = fields.String(required=False)
    request = fields.Nested(TransactionRequestSchema)
    response = fields.Nested(TransactionResponseSchema)


class TransactionAuditMsgDetailsSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    rule_code = fields.String(required=False)
    severity = fields.String(required=False)


class TransactionAuditMsgSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    rule_code =fields.String(required=False)
    text = fields.String(required=False)
    details = fields.Nested(TransactionAuditMsgDetailsSchema, many=True)


class TransactionAuditSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    engine = fields.String(required=False)
    connector = fields.String(required=False)
    mode = fields.String(required=False)
    messages = fields.Nested(TransactionAuditMsgSchema, many=True)


class TransactionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String(required=False)
    logtime = fields.DateTime(format=DATETIME_FMT)
    unique_id = fields.String(required=False)
    server_id = fields.String(required=False)
    action = fields.String(required=False)
    limit_req_status = fields.String(required=False)
    user_agent = fields.Nested(TransactionUserAgentSchema)
    source = fields.Nested(TransactionSourceSchema)
    destination = fields.Nested(TransactionDestinationSchema)
    http = fields.Nested(TransactionHttpSchema)
    audit = fields.Nested(TransactionAuditSchema)
    route_name = fields.String(required=False)
    archived = fields.Boolean(required=False)
    sensor = fields.Nested(SensorSchema)
    upstream = fields.Nested(UpstreamSchema)
    service = fields.Nested(ServiceSchema)


class DashboardServiceRequests(Schema):
    class Meta:
        unknown = EXCLUDE

    service = fields.Nested(ServiceSchema)
    actions = fields.List(fields.Integer())
    bytes_in = fields.Integer(required=False)
    bytes_out = fields.Integer(required=False)
    latency = fields.Integer(required=False)
    tpm = fields.Integer(required=False)


class DashboardRequests(Schema):
    class Meta:
        unknown = EXCLUDE

    logtime = fields.DateTime(format=DATETIME_FMT)
    actions = fields.List(fields.Integer())


class TransactionDao(MongoDAO):
    def __init__(self):
        super().__init__("transaction", schema=TransactionSchema)

    def _load(self, vo):
        if vo:
            super()._load(vo)
            if "sensor_id" in vo:
                dao = SensorDao()
                vo.update({"sensor": dao.get_descr_by_id(vo.pop("sensor_id"))})
            if "service_id" in vo:
                dao = ServiceDao()
                vo.update({"service": dao.get_descr_by_id(vo.pop("service_id"))})
            if "upstream_id" in vo:
                dao = UpstreamDao()
                vo.update({"upstream": dao.get_descr_by_id(vo.pop("upstream_id"))})

    def _unload(self, vo):
        super()._unload(vo)
        if "sensor" in vo:
            sensor = vo.pop("sensor")
            if sensor["_id"]:
                vo.update({"sensor_id": ObjectId(sensor["_id"])})

        if "upstream" in vo:
            upstream = vo.pop("upstream")
            if upstream["_id"]:
                vo.update({"upstream_id": ObjectId(upstream["_id"])})

        if "service" in vo:
            service = vo.pop("service")
            if service["_id"]:
                vo.update({"service_id": ObjectId(service["_id"])})

    def purge_before_date(self, purge_date):
        query = {
            "logtime": {
                "$lte": purge_date
            }
        }
        rs = self.collection.delete_many(query)
        logger.debug(query)
        return rs.deleted_count

    def get_by_server_unique(self, server_id, unique_id):
        query = {"server_id": server_id, "unique_id": unique_id}
        logger.debug(query)
        rs = self.collection.find_one(query)
        self._load(rs)
        return rs

    def update_by_server_unique(self, server_id, unique_id, vo):
        query = {"$set": vo}
        logger.debug(query)
        rs = self.collection.update_one(
            {"server_id": server_id, "unique_id": unique_id}, query
        )
        return rs.modified_count > 0

    def get_trn_telemetry(self, dt_start):
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
                    "_id": {
                        "year": {"$year": "$logtime"},
                        "month": {"$month": "$logtime"},
                        "day": {"$dayOfMonth": "$logtime"},
                        "hour": {"$hour": "$logtime"},
                        "minute": {"$minute": "$logtime"},
                        "server_id": "$server_id",
                        "service_id": "$service_id",
                    },
                    "net_recv": { "$sum": "$http.request.bytes" },
                    "net_send": { "$sum": "$http.response.bytes" },
                    "req_total": { "$sum": 1 }
                }
            }
        ]
        logger.debug(query)
        rs = self.collection.aggregate(query)
        records=list(rs)

        service_dao = ServiceDao()

        if records:
            for s in records:
                dtj = s.pop("_id")
                dt = datetime(
                    dtj["year"], dtj["month"], dtj["day"], dtj["hour"], dtj["minute"]
                ).astimezone(tz=TZ)
                s.update(
                    {
                        "logtime": dt,
                        "server_id": dtj['server_id'],
                        "service": service_dao.get_descr_by_id(dtj['service_id'])
                    }
                )
                logger.debug(s)
        return records

    def get_tpm(self, dt_start, dt_end, filters):
        query = [
            {
                "$match": {
                    "logtime": {
                        "$gte": dt_start,
                        "$lt": dt_end,
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$logtime"},
                        "month": {"$month": "$logtime"},
                        "day": {"$dayOfMonth": "$logtime"},
                        "hour": {"$hour": "$logtime"},
                        "minute": {"$minute": "$logtime"},
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        if filters:
            for f in filters:
                query[0]["$match"].update(f)
        logger.debug(query)
        rs = self.collection.aggregate(query)
        return list(rs)

    def get_all(
            self, pagination=None, dt_start=None, dt_end=None, filters=None
    ):
        query = [
            {
                "$match": {

                }
            },
            {"$sort": {"logtime": -1}},
        ]
        if dt_start and dt_end:
            query[0]["$match"].update({"logtime": {
                "$gte": dt_start,
                "$lte": dt_end
            }})

        if pagination:
            query.append(
                {
                    "$facet": {
                        "data": [
                            {"$skip": ((pagination['page'] - 1) * pagination['per_page'])},
                            {"$limit": pagination['per_page']},
                        ],
                        "pagination": [{"$count": "total"}],
                    }
                }
            )
        else:
            query.append({"$facet": {"data": []}})
        if filters:
            for f in filters:
                query[0]["$match"].update(f)

        logger.debug(query)
        rs = list(self.collection.aggregate(query))[0]
        return self._fetch_all(rs, pagination=pagination)
