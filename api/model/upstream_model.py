from enum import Enum

from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class Protocol(Enum):
    AJP = ("AJP",)
    HTTP = ("HTTP",)
    HTTPS = "HTTPS"

    def __str__(self):
        return str(self.name)

class UpstreamTargetSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    host = fields.String()
    port = fields.Integer()
    weight = fields.Integer()

class UpstreamPersistSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    type = fields.String(required=False)
    cookie_name = fields.String(required=False)
    cookie_domain = fields.String(required=False)
    cookie_path = fields.String(required=False)
    cookie_expire = fields.Integer(required=False)

class UpstreamSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    description = fields.String()
    retry = fields.Integer()
    retry_timeout = fields.Integer()
    conn_timeout = fields.Integer()
    protocol = fields.String()
    script_path = fields.String() #fastcgi
    type = fields.String() # backend, static
    targets = fields.List(fields.Nested(UpstreamTargetSchema))
    persist = fields.Nested(UpstreamPersistSchema)
    index = fields.String()
    content = fields.Raw()
    healthy = fields.Boolean() #Virtual

class UpstreamTargetStatusSchema(Schema):
    class Meta:
        unknown = EXCLUDE
    endpoint = fields.String()
    healthy = fields.Boolean()

class UpstreamStatusSchema(Schema):
    class Meta:
        unknown = EXCLUDE
    _id = fields.String()
    name = fields.String()
    healthy = fields.Boolean()
    targets=fields.List(fields.Nested(UpstreamTargetStatusSchema))

class NodeStatusSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    scn = fields.String()
    version = fields.String()
    upstreams = fields.List(fields.Nested(UpstreamStatusSchema))
    healthy = fields.Boolean() # Virtual
    role= fields.String()
    last_check = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)
    net_recv = fields.Integer(required=False)   # Virtual
    net_send = fields.Integer(required=False)   # Virtual
    online =  fields.Boolean()                  # Virtual

class NodeStatusDao(MongoDAO):
    def __init__(self):
        super().__init__("nodes", schema=NodeStatusSchema)

    def get_upstream_healthy(self,upstream_id):
        query = {"upstreams._id": ObjectId(upstream_id)}
        rows = list(self.collection.find(query))
        for r in rows:
            if not r['healthy']:
                return False
        return True

    def _unload(self, vo):
        super()._unload(vo)
        if "upstreams" in vo:
            ups = vo.pop('upstreams')
            for u in ups:
                u.update({"_id":ObjectId(u['_id'])})
            vo.update({"upstreams":ups})
        return vo

class UpstreamDao(MongoDAO):
    def __init__(self):
        super().__init__("upstream", schema=UpstreamSchema)

    def get_all_by_type(self, t):
        query={"type": {"$eq": t}}
        rows = list(self.collection.find(query))
        for r in rows:
            self._load(r)
        return rows

    def _unload(self, vo):
        super()._unload(vo)
        if "type" not in vo:
            vo.update({"type":"backend"})