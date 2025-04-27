from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.feed_model import FeedSchema
from model.mongo_base_model import MongoDAO
from tools.network_tool import NetworkTool


class RBLSchema(Schema):
    """
    Schema for RBL validation and serialization.
    
    This schema defines the structure and validation rules for RBL documents.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    net_start = fields.String()
    net_end = fields.String()
    network = fields.String()
    version = fields.Integer()
    src_type = fields.String()  # feed, pass_list, jail
    src_type_id = fields.String()  # _id from source


class RBLDao(MongoDAO):
    """
    DAO for managing RBL (Real-time Blackhole List) data.
    
    This class extends MongoDAO to provide specific operations
    related to RBL management, including IP checking and provider management.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'rbl' collection and schema.
        """
        super().__init__("rbl", schema=FeedSchema)


    def check_by_ip(self, ip: str, sensor: Dict[str, Any]) -> Dict[str, bool]:
        """
        Checks if an IP address is blocked by any RBL providers.
        
        Args:
            ip (str): IP address to check
            sensor (Dict[str, Any]): Sensor configuration with provider lists
            
        Returns:
            Dict[str, bool]: Dictionary with 'blocked' status
            
        Raises:
            PyMongoError: If an error occurs during the check operation
        """
        try:
            ip_id = NetworkTool.id(ip)

            bl_providers = []
            if "block" in sensor:
                for sb in sensor["block"]:
                    if sb:
                        bl_providers.append(ObjectId(sb["_id"]))

            if "jails" in sensor:
                for sb in sensor["jails"]:
                    if sb:
                        bl_providers.append(ObjectId(sb["_id"]))

            per_providers = []
            if "permit" in sensor:
                for sb in sensor["permit"]:
                    if sb:
                        per_providers.append(ObjectId(sb["_id"]))

            query = [
                {
                    "$match": {
                        "net_start": {"$lte": ip_id},
                        "net_end": {"$gte": ip_id},
                        "version": {"$eq": 4 if NetworkTool.is_ipv4(ip) else 6},
                    }
                },
                {
                    "$facet": {
                        "pass": [
                            {
                                "$match": {
                                    "action": "pass",
                                    "provider_id": {"$in": per_providers},
                                }
                            }
                        ],
                        "deny": [
                            {
                                "$match": {
                                    "action": "deny",
                                    "provider_id": {"$in": list(set(bl_providers))},
                                }
                            }
                        ],
                    }
                },
                {
                    "$project": {
                        "result": {
                            "$cond": {
                                "if": {"$gt": [{"$size": "$pass"}, 0]},
                                "then": [],
                                "else": "$deny",
                            }
                        }
                    }
                },
                {"$unwind": "$result"},
                {"$replaceRoot": {"newRoot": "$result"}},
            ]
            logger.debug(query)
            rs = list(self.collection.aggregate(query))
            return {"blocked": (len(rs) > 0)}
        except Exception as e:
            logger.error(f"Error checking IP in RBL: {str(e)}")
            raise

    def delete_by_provider(self, provider_type: str, provider_id: str) -> None:
        """
        Deletes all RBL entries for a specific provider.
        
        Args:
            provider_type (str): Type of provider
            provider_id (str): ID of the provider
            
        Raises:
            PyMongoError: If an error occurs during the delete operation
        """
        try:
            query = {
                "$and": [
                    {"provider_type": {"$eq": provider_type}},
                    {"provider_id": {"$eq": ObjectId(provider_id)}},
                ]
            }
            self.collection.delete_many(query)
        except Exception as e:
            logger.error(f"Error deleting RBL entries by provider: {str(e)}")
            raise

    def delete_expired(self, provider_type: str, provider_id: str, bantime_limit: datetime) -> None:
        """
        Deletes expired RBL entries for a specific provider.
        
        Args:
            provider_type (str): Type of provider
            provider_id (str): ID of the provider
            bantime_limit (datetime): Cutoff date for expiration
            
        Raises:
            PyMongoError: If an error occurs during the delete operation
        """
        try:
            query = {
                "$and": [
                    {"provider_type": {"$eq": provider_type}},
                    {"provider_id": {"$eq": ObjectId(provider_id)}},
                    {"banned_on": {"$lte": bantime_limit}},
                ]
            }
            logger.debug(query)
            self.collection.delete_many(query)
        except Exception as e:
            logger.error(f"Error deleting expired RBL entries: {str(e)}")
            raise
