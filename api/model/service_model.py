from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.certificate_model import CertificateDao, CertificateSchema
from api.model.mongo_base_model import MongoDAO
from api.model.sensor_model import SensorSchema, SensorDao
from api.model.upstream_model import UpstreamDao, UpstreamSchema


class HeaderSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    content = fields.String()


class BindSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    port = fields.Integer()
    protocol = fields.String()
    ssl_upgrade = fields.Boolean()


class RedirectSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    code = fields.Integer()
    url = fields.String()


class RouteFilterSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    description = fields.String()
    type = fields.String()  # SSL_CLIENT_AUTH, LDAP_AUTH
    ssl_dn_regex = fields.String()
    ssl_fingerprints = fields.List(fields.String())
    ldap_host = fields.String()
    ldap_base_dn = fields.String()
    ldap_bind_dn = fields.String()
    ldap_bind_password = fields.String()
    ldap_group_dn = fields.String()


class RouteSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    type = fields.String()
    paths = fields.List(fields.String())
    methods = fields.List(fields.String())
    upstream = fields.Nested(UpstreamSchema)
    redirect = fields.Nested(RedirectSchema)
    sensor = fields.Nested(SensorSchema)
    monitor_only = fields.Boolean()
    cache_methods = fields.List(fields.String())
    filters = fields.Nested(RouteFilterSchema, many=True)


class ServiceSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    body_limit = fields.Integer()
    timeout = fields.Integer()
    inspect_level = fields.Integer()
    active = fields.Boolean()
    inbound_score = fields.Integer()
    outbound_score = fields.Integer()
    buffer = fields.Integer()
    bindings = fields.Nested(BindSchema, many=True)
    headers = fields.Nested(HeaderSchema, many=True)
    routes = fields.Nested(RouteSchema, many=True)
    compression = fields.Boolean()
    rate_limit = fields.Boolean()
    rate_limit_per_sec = fields.Integer()
    sans = fields.List(fields.String())
    ssl_protocols = fields.List(fields.String())
    certificate = fields.Nested(CertificateSchema)
    ssl_client_ca = fields.String()
    ssl_client_auth = fields.Boolean(default=False)


class RouteFilterDao(MongoDAO):
    def __init__(self):
        super().__init__("route_filters", schema=RouteFilterSchema)


class ServiceDao(MongoDAO):
    def __init__(self):
        super().__init__("service", schema=ServiceSchema)

    def _unload(self, vo):
        super()._unload(vo)

        if "certificate" in vo:
            certificate = vo.pop("certificate")
            vo.update({"certificate_id": ObjectId(certificate["_id"])})

        if "routes" in vo:
            for route in vo["routes"]:
                if "type" not in route or len(route["type"]) <= 0:
                    route.update({"type": "upstream"})

                if "filters" in route:
                    fs_ids = []
                    for b in route.pop("filters"):
                        fs_ids.append(ObjectId(b["_id"]))
                    route.update({"filter_ids": fs_ids})

                if "upstream" in route["type"]:
                    upstream = route.pop("upstream")
                    route.update({"upstream_id": ObjectId(upstream["_id"])})

                if "sensor" in route:
                    sensor = route.pop("sensor")
                    route.update({"sensor_id": ObjectId(sensor["_id"])})

    def _load(self, vo):
        super()._load(vo)

        if "certificate_id" in vo:
            crt_id = vo.pop("certificate_id")
            vo.update({"certificate": CertificateDao().get_by_id(ObjectId(crt_id))})

        if "routes" in vo:
            for route in vo["routes"]:
                if "type" not in route:  # default value for compatibility
                    route.update({"type": "upstream"})

                if "filter_ids" in route:
                    fs = []
                    dao = RouteFilterDao()
                    for b in route.pop("filter_ids"):
                        fs.append(dao.get_by_id(str(b)))
                    route.update({"filters": fs})

                if "upstream" in route["type"]:
                    upstream_id = route.pop("upstream_id")
                    ups_dao = UpstreamDao()
                    route.update({"upstream": ups_dao.get_descr_by_id(upstream_id)})

                if "sensor_id" in route:
                    sensor_id = route.pop("sensor_id")
                    sen_dao = SensorDao()
                    route.update({"sensor": sen_dao.get_descr_by_id(sensor_id)})

    def get_by_sans(self, sans, active=None):
        query = {"sans": {"$in": sans}}
        if active is not None:
            query["$and"].append({"active": {"$eq": active}})

        logger.debug(query)
        vo = self.collection.find_one(query)
        if vo:
            self._load(vo)
        return vo

    def get_all_for_renew(self, ssl_provider):
        query = {"provider": {"$in": ssl_provider}}
        logger.debug(query)
        rows = list(self.collection.find(query))
        for e in rows:
            self._load(e)
        return rows

    def getall_by_certificate_id(self, certificate_id):
        query = {"certificate_id": ObjectId(certificate_id), "active": True}
        logger.debug(query)
        rows = list(self.collection.find(query))
        for e in rows:
            self._load(e)
        return rows
