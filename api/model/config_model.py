from typing import Dict, Any, Optional

from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.mongo_base_model import MongoDAO


class ConfigArchiveSchema(Schema):
    """
    Schema for archive configuration validation and serialization.
    
    This schema defines the structure and validation rules for archive configuration.
    """
    enabled = fields.Boolean()
    archive_after = fields.Integer()  # minutes
    purge_after = fields.Integer()  # days
    type = fields.String()  # elastic_search, opensearch, syslog
    url = fields.String()
    username = fields.String()
    password = fields.String()


class ConfigPurgeSchema(Schema):
    """
    Schema for purge configuration validation and serialization.
    
    This schema defines the structure and validation rules for purge configuration.
    """
    enabled = fields.Boolean()
    purge_after = fields.Integer()  # days

class ConfigTelemetrySchema(Schema):
    """
    Schema for purge configuration validation and serialization.
    
    This schema defines the structure and validation rules for purge configuration.
    """
    enabled = fields.Boolean()
    url = fields.String()


class ConfigSchema(Schema):
    """
    Schema for main configuration validation and serialization.
    
    This schema defines the structure and validation rules for the main configuration.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    cluster_id = fields.String()
    maxmind_key = fields.String()
    ca_certificate = fields.String()
    ca_private = fields.String()
    acme_directory_url = fields.String()
    archive = fields.Nested(ConfigArchiveSchema)
    purge = fields.Nested(ConfigPurgeSchema)
    telemetry = fields.Nested(ConfigTelemetrySchema)


class ConfigDao(MongoDAO):
    """
    DAO for managing system configuration.
    
    This class extends MongoDAO to provide specific operations
    related to system configuration management.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'config' collection and schema.
        """
        super().__init__("config", schema=ConfigSchema)


    def get_active(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the active configuration.
        
        Returns:
            Optional[Dict[str, Any]]: Active configuration document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            rs = self.collection.find_one({})
            self._to_dict(rs)
            return rs
        except Exception as e:
            logger.error(f"Error retrieving active configuration: {str(e)}")
            raise


class ChangeDao(MongoDAO):
    """
    DAO for managing configuration changes.
    
    This class extends MongoDAO to provide specific operations
    related to configuration change tracking.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'changes' collection.
        """
        super().__init__("changes")

