from typing import Dict, Any, Optional

from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.mongo_base_model import MongoDAO


class OIDCToken(Schema):
    """
    Schema for OIDC token validation and serialization.
    
    This schema defines the structure and validation rules for OIDC tokens.
    """
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(load_default="Bearer", dump_default="Bearer")
    expires_in = fields.Integer()
    provider = fields.String()


class UserSchema(Schema):
    """
    Schema for user validation and serialization.
    
    This schema defines the structure and validation rules for user documents.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    email = fields.String()
    password = fields.String()
    locale = fields.String(required=False)
    role = fields.String()


class UserDao(MongoDAO):
    """
    DAO for managing user data.
    
    This class extends MongoDAO to provide specific operations
    related to user management, including retrieval by email.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'users' collection and schema.
        """
        super().__init__("users", schema=UserSchema)


    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user by their email address.
        
        Args:
            email (str): User's email address
            
        Returns:
            Optional[Dict[str, Any]]: User document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"email": email}
            logger.debug(query)
            v = self.collection.find_one(query)
            super()._to_dict(v)
            return v
        except Exception as e:
            logger.error(f"Error retrieving user by email: {str(e)}")
            raise
