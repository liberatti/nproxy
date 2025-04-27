from typing import Dict, Any, List, Optional
from datetime import datetime
from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class TelemetryTrnSchema(Schema):
    """
    Schema for telemetry transaction validation and serialization.
    
    This schema defines the structure and validation rules for telemetry transactions.
    """
    class Meta:
        unknown = EXCLUDE

    logtime = fields.DateTime(format=DATETIME_FMT)
    server_id = fields.String(required=False)

    net_recv = fields.Integer(required=False)
    net_send = fields.Integer(required=False)
    req_total = fields.Integer(required=False)
    latency = fields.Float(required=False)


class TelemetryTrnDao(MongoDAO):
    """
    DAO for managing telemetry data.
    
    This class extends MongoDAO to provide specific operations
    related to telemetry data management and aggregation.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'telemetry' collection and schema.
        """
        super().__init__("telemetry", schema=TelemetryTrnSchema)


    def get_by_logtime(self, dt_start: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves aggregated telemetry data from a specific start time.
        
        Args:
            dt_start (datetime): Start time for data aggregation
            
        Returns:
            List[Dict[str, Any]]: List of aggregated telemetry records
            
        Raises:
            PyMongoError: If an error occurs during the aggregation operation
        """
        try:
            query = [
                {"$match": {"logtime": {"$gte": dt_start}}},
                {
                    "$group": {
                        "_id": "null",
                        "net_recv": {"$sum": "$net_recv"},
                        "net_send": {"$sum": "$net_send"},
                        "req_total": {"$sum": "$req_total"},
                        "latency": {"$avg": "$latency"},
                    }
                },
            ]
            logger.debug(query)
            rs = self.collection.aggregate(query)
            return list(rs)
        except Exception as e:
            logger.error(f"Error retrieving telemetry by logtime: {str(e)}")
            raise
