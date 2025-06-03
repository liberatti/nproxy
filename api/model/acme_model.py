from datetime import datetime
from typing import Optional, Dict, Any
from common_utils import logger
from model.mongo_base_model import MongoDAO


class ChallengeDao(MongoDAO):
    """
    DAO for managing ACME challenges.
    
    This class extends MongoDAO to provide specific operations
    related to ACME challenges, including key management
    and cleanup of expired challenges.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'challenge' collection.
        """
        super().__init__("challenge")


    def delete_issued_before(self, dt: datetime) -> int:
        """
        Removes challenges issued before the specified date.
        
        Args:
            dt (datetime): Cutoff date for removal
            
        Returns:
            int: Number of documents removed
            
        Raises:
            PyMongoError: If an error occurs during the delete operation
        """
        try:
            result = self.collection.delete_many({"issued": {"$lt": dt}})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error removing old challenges: {str(e)}")
            raise

    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a challenge by its key.
        
        Args:
            key (str): Challenge key
            
        Returns:
            Optional[Dict[str, Any]]: Challenge document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            rs = self.collection.find_one({"key": key})
            self._to_dict(rs)
            return rs
        except Exception as e:
            logger.error(f"Error retrieving challenge by key: {str(e)}")
            raise
