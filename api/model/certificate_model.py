from datetime import datetime, timedelta
from typing import Dict, Any, List

from marshmallow import EXCLUDE, Schema, fields

from common_utils import replace_tz, logger
from model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class CertificateSchema(Schema):
    """
    Schema for certificate validation and serialization.
    
    This schema defines the structure and validation rules for certificate documents.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    subjects = fields.List(fields.String())
    chain = fields.String()
    certificate = fields.String()
    private_key = fields.String()
    ssl_client_ca = fields.String()
    not_before = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)
    not_after = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)
    status = fields.String(required=False)
    provider = fields.String(required=False)
    force_renew = fields.Boolean(required=False, load_default=False, dump_default=False)


class CertificateDao(MongoDAO):
    """
    DAO for managing SSL/TLS certificates.
    
    This class extends MongoDAO to provide specific operations
    related to certificate management, including status tracking
    and certificate persistence.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'certificate' collection and schema.
        """
        super().__init__("certificate", schema=CertificateSchema)

    def count_by_status(self) -> Dict[str, int]:
        """
        Counts certificates by their status.
        
        Returns:
            Dict[str, int]: Dictionary with status as key and count as value
            
        Raises:
            PyMongoError: If an error occurs during the aggregation
        """
        try:
            query = [
                {"$facet": {"data": [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]}}
            ]
            rs = list(self.collection.aggregate(query))[0]
            rows = rs.get("data", [])
            return {rows[0]["_id"]: rows[0]["count"], rows[1]["_id"]: rows[1]["count"]}
        except Exception as e:
            logger.error(f"Error counting certificates by status: {str(e)}")
            raise

    def persist(self, o: Dict[str, Any]) -> str:
        """
        Persists a new certificate with default dates if not provided.
        
        Args:
            o (Dict[str, Any]): Certificate data dictionary
            
        Returns:
            str: ID of the inserted certificate
            
        Raises:
            PyMongoError: If an error occurs during the insert operation
        """
        try:
            default_date = (
                replace_tz((datetime.now() - timedelta(days=1)))
                .replace(microsecond=0)
            )
            if "not_after" not in o:
                o.update({"not_after": default_date})

            if "not_before" not in o:
                o.update({"not_before": default_date})
            return super().persist(o)
        except Exception as e:
            logger.error(f"Error persisting certificate: {str(e)}")
            raise
