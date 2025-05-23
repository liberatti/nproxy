from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.feed_model import FeedDao, FeedSchema
from api.model.jail_model import JailDao
from api.model.mongo_base_model import MongoDAO


class SensorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    description = fields.String()
    categories = fields.List(fields.String())
    exclusions = fields.List(fields.Integer())
    permit = fields.Nested(FeedSchema, many=True)
    block = fields.Nested(FeedSchema, many=True)
    geo_block_list = fields.List(fields.String())
    jails = fields.Nested(FeedSchema, many=True)


class SensorDao(MongoDAO):
    def __init__(self):
        super().__init__("sensor", schema=SensorSchema)

    def _load(self, vo):
        if vo:
            super()._load(vo)
            if "block_ids" in vo:
                block = []
                dao = FeedDao()
                for b in vo.pop("block_ids"):
                    block.append(dao.get_descr_by_id(str(b)))
                vo.update({"block": block})

            if "permit_ids" in vo:
                permit = []
                dao = FeedDao()
                for b in vo.pop("permit_ids"):
                    permit.append(dao.get_descr_by_id(str(b)))
                vo.update({"permit": permit})

            if "jail_ids" in vo:
                jails = []
                dao = JailDao()
                for b in vo.pop("jail_ids"):
                    jails.append(dao.get_descr_by_id(str(b)))
                vo.update({"jails": jails})

    def _unload(self, vo):
        if vo:
            super()._unload(vo)
            if "block" in vo:
                block_ids = []
                for b in vo.pop("block"):
                    block_ids.append(ObjectId(b["_id"]))
                vo.update({"block_ids": block_ids})

            if "permit" in vo:
                permit_ids = []
                for b in vo.pop("permit"):
                    permit_ids.append(ObjectId(b["_id"]))
                vo.update({"permit_ids": permit_ids})
            if "jails" in vo:
                jail_ids = []
                for b in vo.pop("jails"):
                    jail_ids.append(ObjectId(b["_id"]))
                vo.update({"jail_ids": jail_ids})

    def get_ids_by_jail(self, jail_id):
        query = {"jail_ids": ObjectId(jail_id)}
        logger.debug(query)
        rows = list(self.collection.find(query))
        return [str(doc["_id"]) for doc in rows]
