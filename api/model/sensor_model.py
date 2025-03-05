from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.model.dictionary_model import DataObjectSchema
from api.model.dictionary_model import DictionaryDao
from api.model.mongo_base_model import MongoDAO


class SensorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    description = fields.String()
    categories = fields.List(fields.String())
    exclusions = fields.List(fields.Integer())
    permit = fields.Nested(DataObjectSchema, many=True)
    block = fields.Nested(DataObjectSchema, many=True)


class SensorDao(MongoDAO):
    def __init__(self):
        super().__init__("sensor", schema=SensorSchema)

    def _load(self, vo):
        if vo:
            super()._load(vo)
            if "block_ids" in vo:
                block = []
                dao = DictionaryDao()
                for b in vo.pop("block_ids"):
                    block.append(dao.get_descr_by_id(str(b)))
                vo.update({"block": block})

            if "permit_ids" in vo:
                permit = []
                dao = DictionaryDao()
                for b in vo.pop("permit_ids"):
                    permit.append(dao.get_descr_by_id(str(b)))
                vo.update({"permit": permit})

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
