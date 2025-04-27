from datetime import datetime
from typing import Dict, Any, List

from marshmallow import EXCLUDE, Schema, fields

from common_utils import replace_tz, logger
from model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class JailEntrySchema(Schema):
    """
    Schema for jail entry validation and serialization.
    
    This schema defines the structure and validation rules for jail entries.
    """
    class Meta:
        unknown = EXCLUDE

    ipaddr = fields.String()
    banned_on = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)


class JailRulesSchema(Schema):
    """
    Schema for jail rules validation and serialization.
    
    This schema defines the structure and validation rules for jail rules.
    """
    class Meta:
        unknown = EXCLUDE

    field = fields.String()  # header, request_line, source
    regex = fields.String()


class JailSchema(Schema):
    """
    Schema for jail validation and serialization.
    
    This schema defines the structure and validation rules for jail documents.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    bantime = fields.Integer()
    occurrence = fields.Integer()  # 10, 20 ....
    interval = fields.Integer()  # seconds
    content = fields.Nested(JailEntrySchema, many=True)
    rules = fields.Nested(JailRulesSchema, many=True)


class JailDao(MongoDAO):
    """
    DAO for managing jail data.
    
    This class extends MongoDAO to provide specific operations
    related to jail management, including retrieval by type
    and persistence of jail entries.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'jail' collection and schema.
        """
        super().__init__("jail", schema=JailSchema)


    def get_by_type(self, t: str) -> List[Dict[str, Any]]:
        """
        Retrieves jails by their type.
        
        Args:
            t (str): Jail type to search for
            
        Returns:
            List[Dict[str, Any]]: List of jail documents matching the type
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"type": t}
            logger.debug(query)
            rows = list(self.collection.find(query))
            for e in rows:
                 self._to_dict(e)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving jails by type: {str(e)}")
            raise

    def persist(self, vo: Dict[str, Any]) -> str:
        """
        Persists a new jail with default dates for entries if not provided.
        
        Args:
            vo (Dict[str, Any]): Jail data dictionary
            
        Returns:
            str: ID of the inserted jail
            
        Raises:
            PyMongoError: If an error occurs during the insert operation
        """
        try:
            default_date = replace_tz(datetime.now()).replace(microsecond=0)

            for c in vo["content"]:
                if "banned_on" not in c:
                    c.update({"banned_on": default_date})
            return super().persist(vo)
        except Exception as e:
            logger.error(f"Error persisting jail: {str(e)}")
            raise
