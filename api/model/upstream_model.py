from enum import Enum
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields
from datetime import datetime
from common_utils import logger
from model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class Protocol(Enum):
    """
    Enumeration for supported upstream protocols.
    
    This enum defines the available protocols for upstream connections.
    """
    AJP = ("AJP",)
    HTTP = ("HTTP",)
    HTTPS = "HTTPS"

    def __str__(self):
        """Returns the string representation of the protocol."""
        return str(self.name)


class UpstreamTargetSchema(Schema):
    """
    Schema for upstream target validation and serialization.
    
    This schema defines the structure and validation rules for upstream targets.
    """
    class Meta:
        unknown = EXCLUDE

    host = fields.String()
    port = fields.Integer()
    weight = fields.Integer()


class UpstreamPersistSchema(Schema):
    """
    Schema for upstream persistence validation and serialization.
    
    This schema defines the structure and validation rules for upstream persistence settings.
    """
    class Meta:
        unknown = EXCLUDE

    type = fields.String(required=False)
    cookie_name = fields.String(required=False)
    cookie_domain = fields.String(required=False)
    cookie_path = fields.String(required=False)
    cookie_expire = fields.Integer(required=False)


class UpstreamSchema(Schema):
    """
    Schema for upstream validation and serialization.
    
    This schema defines the structure and validation rules for upstream configurations.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    description = fields.String()
    retry = fields.Integer()
    retry_timeout = fields.Integer()
    conn_timeout = fields.Integer()
    protocol = fields.String()
    script_path = fields.String()  # fastcgi
    type = fields.String()  # backend, static
    targets = fields.List(fields.Nested(UpstreamTargetSchema))
    persist = fields.Nested(UpstreamPersistSchema)
    index = fields.String()
    content = fields.Raw()
    healthy = fields.Boolean()  # Virtual


class UpstreamTargetStatusSchema(Schema):
    """
    Schema for upstream target status validation and serialization.
    
    This schema defines the structure and validation rules for upstream target status information.
    """
    class Meta:
        unknown = EXCLUDE

    endpoint = fields.String()
    healthy = fields.Boolean()


class UpstreamStatusSchema(Schema):
    """
    Schema for upstream status validation and serialization.
    
    This schema defines the structure and validation rules for upstream status information.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    healthy = fields.Boolean()
    targets = fields.List(fields.Nested(UpstreamTargetStatusSchema))


class NodeStatusSchema(Schema):
    """
    Schema for node status validation and serialization.
    
    This schema defines the structure and validation rules for node status information.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    scn = fields.String()
    version = fields.String()
    upstreams = fields.List(fields.Nested(UpstreamStatusSchema))
    healthy = fields.Boolean()  # Virtual
    role = fields.String()
    last_check = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)
    net_recv = fields.Integer(required=False)  # Virtual
    net_send = fields.Integer(required=False)  # Virtual
    apply_active = fields.Boolean(required=False, dump_default=False)
    apply_pendding = fields.List(fields.String(), required=False)

class NodeStatusDao(MongoDAO):
    """
    DAO for managing node status information.
    
    This class extends MongoDAO to provide specific operations
    related to node status management and monitoring.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'nodes' collection and schema.
        """
        super().__init__("nodes", schema=NodeStatusSchema)

    def purge_before_date(self, last_check: datetime) -> int:
        """
        Purges transactions older than the specified date.
        
        Args:
            purge_date (datetime): Cutoff date for purging
            
        Returns:
            int: Number of documents deleted
            
        Raises:
            PyMongoError: If an error occurs during the purge operation
        """
        try:
            query = {"logtime": {"$lte": last_check}}
            rs = self.collection.delete_many(query)
            logger.debug(query)
            return rs.deleted_count
        except Exception as e:
            logger.error(f"Error purging transactions: {str(e)}")
            raise

    def get_upstream_healthy(self, upstream_id: str) -> bool:
        """
        Checks if an upstream is healthy across all nodes.
        
        Args:
            upstream_id (str): Upstream ID to check
            
        Returns:
            bool: True if the upstream is healthy on all nodes, False otherwise
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"upstreams._id": ObjectId(upstream_id)}
            rows = list(self.collection.find(query))
            for r in rows:
                if not r['healthy']:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking upstream health: {str(e)}")
            raise

    def _from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unloads a node status document, converting nested objects to IDs.
        
        Args:
            vo (Dict[str, Any]): Node status document to unload
            
        Returns:
            Dict[str, Any]: Unloaded node status document
        """
        super()._from_dict(vo)
        if "upstreams" in vo:
            ups = vo.pop('upstreams')
            for u in ups:
                u.update({"_id": ObjectId(u['_id'])})
            vo.update({"upstreams": ups})
        return vo


class UpstreamDao(MongoDAO):
    """
    DAO for managing upstream configurations.
    
    This class extends MongoDAO to provide specific operations
    related to upstream management and configuration.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'upstream' collection and schema.
        """
        super().__init__("upstream", schema=UpstreamSchema)


    def get_all_by_type(self, t: str) -> List[Dict[str, Any]]:
        """
        Retrieves all upstreams of a specific type.
        
        Args:
            t (str): Upstream type to filter by
            
        Returns:
            List[Dict[str, Any]]: List of upstream documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"type": {"$eq": t}}
            rows = list(self.collection.find(query))
            for r in rows:
                 self._to_dict(r)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving upstreams by type: {str(e)}")
            raise

    def _from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unloads an upstream document, converting nested objects to IDs.
        
        Args:
            vo (Dict[str, Any]): Upstream document to unload
            
        Returns:
            Dict[str, Any]: Unloaded upstream document
        """
        super()._from_dict(vo)
        if "type" not in vo:
            vo.update({"type": "backend"})
        return vo