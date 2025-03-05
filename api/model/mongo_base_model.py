import json
import pickle

from bson import ObjectId
from marshmallow import Schema, fields

from api.common_utils import logger, config_db


class MongoDAO:

    def __init__(self, collection_name, schema=None):
        self.__DB_NAME__ = "nproxy"
        self.database = getattr(config_db, self.__DB_NAME__)
        self.collection_name = collection_name
        self.collection = self.database[collection_name]
        if schema:
            page_class = type('pagination', (Schema,), {
                'metadata': fields.Nested("PageMetaSchema", many=False),
                'data': fields.Nested(schema, many=True)
            })
            self.pageSchema = page_class()
            self.schema = schema()

    def drop_database(self):
        config_db.drop_database(self.__DB_NAME__)

    def json_load(self, json_data):
        if self.schema:
            return self.schema.load(json_data)
        else:
            return json.load(json_data)

    def json_dump(self, vo):
        return self.schema.dump(vo)

    def _unload(self, vo):
        if vo and "_id" in vo:
            vo.update({"_id": ObjectId(vo["_id"])})

    def _load(self, vo):
        if vo and "_id" in vo:
            vo.update({"_id": str(vo["_id"])})
        return vo

    def _fetch_all(self, rs, pagination=None):
        rows = rs.get("data", [])
        if pagination:
            _meta = rs.get("pagination")
            if not _meta or len(_meta) == 0:
                _meta = [{"total": 0}]
            pagination.update({'total_elements': _meta[0].get("total", 0)})
        else:
            te = len(rows)
            pagination = {
                'total_elements': te,
                'page': 1,
                'per_page': te
            }

        for r in rows:
            self._load(r)
        return dict(
            {
                "metadata": pagination,
                "data": rows,
            }
        )

    def get_all(self, pagination=None, filters=None):
        query = []
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
            query.insert(0, {
                "$match": dict()
            })
            for f in filters:
                query[0]["$match"].update(f)

        logger.debug(query)
        rs = list(self.collection.aggregate(query))[0]
        return self._fetch_all(rs, pagination=pagination)

    def get_descr_by_id(self, _id):
        rs = self.collection.find_one({"_id": ObjectId(_id)})
        if rs and "_id" in rs and "name" in rs:
            return {"_id": str(rs["_id"]), "name": rs["name"]}

    def get_by_id(self, _id):
        if isinstance(_id, ObjectId):
            rs = self.collection.find_one({"_id": _id})
        else:
            rs = self.collection.find_one({"_id": ObjectId(_id)})
        self._load(rs)
        return rs

    def get_by_name(self, name):
        rs = self.collection.find_one({"name": name})
        self._load(rs)
        return rs

    def update_by_id(self, _id, vo):
        self._unload(vo)
        query = {"$set": vo}
        logger.debug(query)
        if isinstance(_id, ObjectId):
            rs = self.collection.update_one({"_id": _id}, query)
        else:
            rs = self.collection.update_one({"_id": ObjectId(_id)}, query)
        self._load(vo)
        return rs.modified_count > 0

    def persist(self, vo):
        if "_id" in vo:
            vo.pop("_id")
        self._unload(vo)
        pk = self.collection.insert_one(vo)
        vo.update({"_id": str(pk.inserted_id)})
        return str(pk.inserted_id)

    def persist_many(self, arr):
        return self.collection.insert_many(arr)

    def delete_by_id(self, _id):
        dr = self.collection.delete_one({"_id": ObjectId(_id)})
        return dr.deleted_count > 0

    def delete_all(self):
        dr = self.collection.delete_many({})
        return dr.deleted_count > 0

    def data_export(self, folder):
        dset = list(self.collection.find())
        logger.info(f"Export {len(dset)} to {folder}/{self.collection_name}.data")
        with open(f"{folder}/{self.collection_name}.data", 'wb') as f:
            pickle.dump(dset, f)

    def data_import(self, folder):
        with open(f"{folder}/{self.collection_name}.data", 'rb') as f:
            dset = pickle.load(f)
            self.collection.delete_many({})
            if len(dset)>0:
                logger.info(f"Import {len(dset)} to {folder}/{self.collection_name}.data")
                self.collection.insert_many(dset)