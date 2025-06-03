from typing import Dict, Any, List, Optional
from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.feed_model import FeedDao, FeedSchema
from model.jail_model import JailDao
from model.mongo_base_model import MongoDAO


class SensorSchema(Schema):
    """
    Schema for sensor validation and serialization.
    
    This schema defines the structure and validation rules for sensor documents.
    """
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
    """
    DAO for managing sensor data.
    
    This class extends MongoDAO to provide specific operations
    related to sensor management, including feed and jail associations.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'sensor' collection and schema.
        """
        super().__init__("sensor", schema=SensorSchema)



    def _to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Loads a sensor document with its associated feeds and jails.
        
        Args:
            vo (Optional[Dict[str, Any]]): Sensor document to load
            
        Returns:
            Optional[Dict[str, Any]]: Loaded sensor document
        """
        if vo:
            super()._to_dict(vo)
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
        return vo

    def _from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unloads a sensor document, converting nested objects to IDs.
        
        Args:
            vo (Dict[str, Any]): Sensor document to unload
            
        Returns:
            Dict[str, Any]: Unloaded sensor document
        """
        if vo:
            super()._from_dict(vo)
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
        return vo

    def get_ids_by_jail(self, jail_id: str) -> List[str]:
        """
        Retrieves sensor IDs associated with a specific jail.
        
        Args:
            jail_id (str): Jail ID to search for
            
        Returns:
            List[str]: List of sensor IDs
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"jail_ids": ObjectId(jail_id)}
            logger.debug(query)
            rows = list(self.collection.find(query))
            return [str(doc["_id"]) for doc in rows]
        except Exception as e:
            logger.error(f"Error retrieving sensor IDs by jail: {str(e)}")
            raise
