import json
import pickle
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from bson import ObjectId
from marshmallow import Schema, fields
from pymongo.errors import PyMongoError

from common_utils import logger, config_db
from config import MONGO_DB


class MongoDAO:
    """
    Base class for MongoDB data access.
    
    This class provides an abstract interface for basic CRUD operations
    and additional functionalities like pagination, data export and import.
    
    Attributes:
        __DB_NAME__ (str): MongoDB database name
        database: MongoDB database instance
        collection_name (str): Collection name
        collection: MongoDB collection reference
        schema: Marshmallow schema for validation and serialization
    """
    
    def __init__(self, collection_name: str, schema: Optional[Schema] = None):
        """
        Initializes the DAO with the specified collection and schema.
        
        Args:
            collection_name (str): MongoDB collection name
            schema (Optional[Schema]): Marshmallow schema for validation
        """
        self.__DB_NAME__ = MONGO_DB
        self.database = getattr(config_db, self.__DB_NAME__)
        self.collection_name = collection_name
        self.collection = self.database[collection_name]
        if schema:
            page_class = type(
                "pagination",
                (Schema,),
                {
                    "metadata": fields.Nested("PageMetaSchema", many=False),
                    "data": fields.Nested(schema, many=True),
                },
            )
            self.pageSchema = page_class()
            self.schema = schema()


    def json_load(self, json_data):
        if self.schema:
            return self.schema.load(json_data)
        else:
            return json.load(json_data)

    def json_dump(self, vo):
        return self.schema.dump(vo)

    def _from_dict(self, vo):
        if vo and "_id" in vo:
            vo.update({"_id": ObjectId(vo["_id"])})

    def _to_dict(self, vo):
        if vo and "_id" in vo:
            vo.update({"_id": str(vo["_id"])})
        return vo

    def _fetch_all(self, rs, pagination=None):
        rows = rs.get("data", [])
        if pagination:
            _meta = rs.get("pagination")
            if not _meta or len(_meta) == 0:
                _meta = [{"total": 0}]
            pagination.update({"total_elements": _meta[0].get("total", 0)})
        else:
            te = len(rows)
            pagination = {"total_elements": te, "page": 1, "per_page": te}

        for r in rows:
             self._to_dict(r)
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
                            {
                                "$skip": (
                                    (pagination["page"] - 1) * pagination["per_page"]
                                )
                            },
                            {"$limit": pagination["per_page"]},
                        ],
                        "pagination": [{"$count": "total"}],
                    }
                }
            )
        else:
            query.append({"$facet": {"data": []}})

        if filters:
            query.insert(0, {"$match": dict()})
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
        self._to_dict(rs)
        return rs

    def get_by_name(self, name):
        rs = self.collection.find_one({"name": name})
        self._to_dict(rs)
        return rs

    def update_by_query(self, query, vo):
        self._from_dict(vo)
        logger.debug(query)
        rs = self.collection.update_one(query, {"$set": vo})
        return rs.modified_count > 0

    def update_by_id(self, _id: Union[str, ObjectId], vo: Dict[str, Any]) -> bool:
        """
        Updates a document by ID.
        
        Args:
            _id (Union[str, ObjectId]): Document ID
            vo (Dict[str, Any]): Dictionary with updated data
            
        Returns:
            bool: True if the document was updated, False otherwise
            
        Raises:
            PyMongoError: If an error occurs during the update operation
        """
        try:
            self._from_dict(vo)
            #vo["updated_at"] = datetime.utcnow() #TODO: Object of type datetime is not JSON serializable
            query = {"$set": vo}
            logger.debug(query)
            if isinstance(_id, ObjectId):
                rs = self.collection.update_one({"_id": _id}, query)
            else:
                rs = self.collection.update_one({"_id": ObjectId(_id)}, query)
            self._to_dict(vo)
            return rs.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating document: {str(e)}")
            raise

    def persist(self, vo: Dict[str, Any]) -> str:
        """
        Persists a new document in the collection.
        
        Args:
            vo (Dict[str, Any]): Dictionary with document data
            
        Returns:
            str: ID of the inserted document
            
        Raises:
            PyMongoError: If an error occurs during the insert operation
        """
        try:
            if "_id" in vo:
                vo.pop("_id")
            #vo["created_at"] = datetime.utcnow() #TODO: Object of type datetime is not JSON serializable
            self._from_dict(vo)
            pk = self.collection.insert_one(vo)
            vo.update({"_id": str(pk.inserted_id)})
            return str(pk.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error persisting document: {str(e)}")
            raise

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
        with open(f"{folder}/{self.collection_name}.data", "wb") as f:
            pickle.dump(dset, f)

    def data_import(self, folder):
        with open(f"{folder}/{self.collection_name}.data", "rb") as f:
            dset = pickle.load(f)
            self.collection.delete_many({})
            if len(dset) > 0:
                logger.info(
                    f"Import {len(dset)} to {folder}/{self.collection_name}.data"
                )
                self.collection.insert_many(dset)
