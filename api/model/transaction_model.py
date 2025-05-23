from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger, replace_tz
from model.mongo_base_model import MongoDAO
from model.sensor_model import SensorSchema, SensorDao
from model.service_model import ServiceSchema, ServiceDao
from model.upstream_model import UpstreamSchema, UpstreamDao
from config import DATETIME_FMT, TZ, TELEMETRY_INTERVAL


class TransactionHeaderSchema(Schema):
    """
    Schema for transaction header validation and serialization.
    
    This schema defines the structure and validation rules for transaction headers.
    """
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=False)
    content = fields.String(required=False)


class TransactionRequestSchema(Schema):
    """
    Schema for transaction request validation and serialization.
    
    This schema defines the structure and validation rules for transaction requests.
    """
    class Meta:
        unknown = EXCLUDE

    method = fields.String(required=False)
    uri = fields.String(required=False)
    bytes = fields.Integer(required=False)
    headers = fields.Nested("TransactionHeaderSchema", many=True, allow_none=True)


class TransactionResponseSchema(Schema):
    """
    Schema for transaction response validation and serialization.
    
    This schema defines the structure and validation rules for transaction responses.
    """
    class Meta:
        unknown = EXCLUDE

    status_code = fields.Integer(required=False)
    bytes = fields.Integer(required=False)
    headers = fields.Nested("TransactionHeaderSchema", many=True, allow_none=True)


class TransactionUserAgentSchema(Schema):
    """
    Schema for user agent validation and serialization.
    
    This schema defines the structure and validation rules for user agent information.
    """
    class Meta:
        unknown = EXCLUDE

    family = fields.String(required=False)
    major = fields.String(required=False)
    minor = fields.String(required=False)


class TransactionGeoSchema(Schema):
    """
    Schema for geo-location validation and serialization.
    
    This schema defines the structure and validation rules for geo-location data.
    """
    class Meta:
        unknown = EXCLUDE

    addr = fields.String(required=False)
    net_start = fields.String(required=False)
    net_end = fields.String(required=False)
    ans_number = fields.String(required=False)
    organization = fields.String(required=False)
    country = fields.String(required=False)


class TransactionSourceSchema(Schema):
    """
    Schema for transaction source validation and serialization.
    
    This schema defines the structure and validation rules for transaction sources.
    """
    class Meta:
        unknown = EXCLUDE

    ip = fields.String(required=False)
    port = fields.String(required=False)
    geo = fields.Nested(TransactionGeoSchema)


class TransactionDestinationSchema(Schema):
    """
    Schema for transaction destination validation and serialization.
    
    This schema defines the structure and validation rules for transaction destinations.
    """
    class Meta:
        unknown = EXCLUDE

    ip = fields.String(required=False)
    port = fields.String(required=False)


class TransactionHttpSchema(Schema):
    """
    Schema for HTTP transaction validation and serialization.
    
    This schema defines the structure and validation rules for HTTP transactions.
    """
    class Meta:
        unknown = EXCLUDE

    duration = fields.Decimal(required=False)
    request_line = fields.String(required=False)
    version = fields.String(required=False)
    request = fields.Nested(TransactionRequestSchema)
    response = fields.Nested(TransactionResponseSchema)


class TransactionAuditMsgDetailsSchema(Schema):
    """
    Schema for audit message details validation and serialization.
    
    This schema defines the structure and validation rules for audit message details.
    """
    class Meta:
        unknown = EXCLUDE

    rule_code = fields.String(required=False)
    severity = fields.String(required=False)


class TransactionAuditMsgSchema(Schema):
    """
    Schema for audit message validation and serialization.
    
    This schema defines the structure and validation rules for audit messages.
    """
    class Meta:
        unknown = EXCLUDE

    rule_code = fields.String(required=False)
    text = fields.String(required=False)
    details = fields.Nested(TransactionAuditMsgDetailsSchema, many=True)


class TransactionAuditSchema(Schema):
    """
    Schema for transaction audit validation and serialization.
    
    This schema defines the structure and validation rules for transaction audits.
    """
    class Meta:
        unknown = EXCLUDE

    engine = fields.String(required=False)
    connector = fields.String(required=False)
    mode = fields.String(required=False)
    messages = fields.Nested(TransactionAuditMsgSchema, many=True)


class TransactionSchema(Schema):
    """
    Schema for transaction validation and serialization.
    
    This schema defines the structure and validation rules for transactions.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String(required=False)
    logtime = fields.DateTime(format=DATETIME_FMT)
    unique_id = fields.String(required=False)
    server_id = fields.String(required=False)
    action = fields.String(required=False)
    limit_req_status = fields.String(required=False)
    geoip_status = fields.String(required=False)
    rbl_status = fields.String(required=False)
    user_agent = fields.Nested(TransactionUserAgentSchema)
    source = fields.Nested(TransactionSourceSchema)
    destination = fields.Nested(TransactionDestinationSchema)
    http = fields.Nested(TransactionHttpSchema)
    audit = fields.Nested(TransactionAuditSchema)
    route_name = fields.String(required=False)
    archived = fields.Boolean(required=False)
    sensor = fields.Nested(SensorSchema)
    upstream = fields.Nested(UpstreamSchema)
    service = fields.Nested(ServiceSchema)
    score = fields.Integer(required=False)


class DashboardServiceRequests(Schema):
    """
    Schema for dashboard service requests validation and serialization.
    
    This schema defines the structure and validation rules for dashboard service requests.
    """
    class Meta:
        unknown = EXCLUDE

    service = fields.Nested(ServiceSchema)
    actions = fields.List(fields.Integer())
    bytes_in = fields.Integer(required=False)
    bytes_out = fields.Integer(required=False)
    latency = fields.Integer(required=False)
    tpm = fields.Integer(required=False)


class DashboardRequests(Schema):
    """
    Schema for dashboard requests validation and serialization.
    
    This schema defines the structure and validation rules for dashboard requests.
    """
    class Meta:
        unknown = EXCLUDE

    logtime = fields.DateTime(format=DATETIME_FMT)
    actions = fields.List(fields.Integer())


class TransactionDao(MongoDAO):
    """
    DAO for managing transactions.
    
    This class extends MongoDAO to provide specific operations
    related to transaction management, including aggregation and filtering.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'transaction' collection and schema.
        """
        super().__init__("transaction", schema=TransactionSchema)


    def _to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Loads a transaction document with its associated resources.
        
        Args:
            vo (Optional[Dict[str, Any]]): Transaction document to load
            
        Returns:
            Optional[Dict[str, Any]]: Loaded transaction document
        """
        if vo:
            super()._to_dict(vo)
            if "sensor_id" in vo:
                dao = SensorDao()
                vo.update({"sensor": dao.get_descr_by_id(vo.pop("sensor_id"))})
            if "service_id" in vo:
                dao = ServiceDao()
                vo.update({"service": dao.get_descr_by_id(vo.pop("service_id"))})
            if "upstream_id" in vo:
                dao = UpstreamDao()
                vo.update({"upstream": dao.get_descr_by_id(vo.pop("upstream_id"))})
        return vo

    def _from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unloads a transaction document, converting nested objects to IDs.
        
        Args:
            vo (Dict[str, Any]): Transaction document to unload
            
        Returns:
            Dict[str, Any]: Unloaded transaction document
        """
        super()._from_dict(vo)
        if "sensor" in vo:
            sensor = vo.pop("sensor")
            if sensor["_id"]:
                vo.update({"sensor_id": ObjectId(sensor["_id"])})

        if "upstream" in vo:
            upstream = vo.pop("upstream")
            if upstream["_id"]:
                vo.update({"upstream_id": ObjectId(upstream["_id"])})

        if "service" in vo:
            service = vo.pop("service")
            if service["_id"]:
                vo.update({"service_id": ObjectId(service["_id"])})
        return vo

    def purge_before_date(self, purge_date: datetime) -> int:
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
            query = {"logtime": {"$lte": purge_date}}
            rs = self.collection.delete_many(query)
            logger.debug(query)
            return rs.deleted_count
        except Exception as e:
            logger.error(f"Error purging transactions: {str(e)}")
            raise

    def get_by_server_unique(self, server_id: str, unique_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a transaction by server ID and unique ID.
        
        Args:
            server_id (str): Server ID
            unique_id (str): Unique transaction ID
            
        Returns:
            Optional[Dict[str, Any]]: Transaction document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"server_id": server_id, "unique_id": unique_id}
            logger.debug(query)
            rs = self.collection.find_one(query)
            self._to_dict(rs)
            return rs
        except Exception as e:
            logger.error(f"Error retrieving transaction by server and unique ID: {str(e)}")
            raise

    def update_by_server_unique(self, server_id: str, unique_id: str, vo: Dict[str, Any]) -> bool:
        """
        Updates a transaction by server ID and unique ID.
        
        Args:
            server_id (str): Server ID
            unique_id (str): Unique transaction ID
            vo (Dict[str, Any]): Updated transaction data
            
        Returns:
            bool: True if the document was updated, False otherwise
            
        Raises:
            PyMongoError: If an error occurs during the update operation
        """
        try:
            query = {"$set": vo}
            logger.debug(query)
            rs = self.collection.update_one(
                {"server_id": server_id, "unique_id": unique_id}, query
            )
            return rs.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating transaction by server and unique ID: {str(e)}")
            raise

    def get_node_bandwidth(self, server_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves bandwidth statistics for a specific node.
        
        Args:
            server_id (str): Server ID
            
        Returns:
            List[Dict[str, Any]]: List of bandwidth statistics
            
        Raises:
            PyMongoError: If an error occurs during the aggregation operation
        """
        try:
            query = [
                {
                    "$match": {
                        "logtime": {"$gte": (datetime.now(TZ) - timedelta(minutes=1))},
                        "server_id": server_id,
                    },
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$logtime"},
                            "month": {"$month": "$logtime"},
                            "day": {"$dayOfMonth": "$logtime"},
                            "hour": {"$hour": "$logtime"},
                            "minute": {"$minute": "$logtime"},
                        },
                        "net_recv": {"$sum": "$http.request.bytes"},
                        "net_send": {"$sum": "$http.response.bytes"},
                        "req_total": {"$sum": 1},
                    }
                },
                {"$limit": 1},
            ]
            logger.debug(query)
            rs = self.collection.aggregate(query)
            return list(rs)
        except Exception as e:
            logger.error(f"Error retrieving node bandwidth: {str(e)}")
            raise

    def get_trn_telemetry(self, dt_start: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves telemetry data for transactions.
        
        Args:
            dt_start (datetime): Start time for telemetry data
            
        Returns:
            List[Dict[str, Any]]: List of telemetry records
            
        Raises:
            PyMongoError: If an error occurs during the aggregation operation
        """
        try:
            query = [
                {
                    "$match": {
                        "logtime": {"$gt": dt_start - timedelta(minutes=TELEMETRY_INTERVAL)}
                    }
                },
                {
                    "$group": {
                        "_id": {"server_id": "$server_id"},
                        "net_recv": {"$sum": "$http.request.bytes"},
                        "net_send": {"$sum": "$http.response.bytes"},
                        "req_total": {"$sum": 1},
                        "latency": {"$avg": "$http.duration"},
                    }
                },
            ]
            logger.debug(query)
            rs = self.collection.aggregate(query)
            records = list(rs)
            if records:
                for s in records:
                    dtj = s.pop("_id")
                    s.update(
                        {
                            "logtime": dt_start,
                            "server_id": dtj["server_id"],
                        }
                    )
            return records
        except Exception as e:
            logger.error(f"Error retrieving transaction telemetry: {str(e)}")
            raise

    def get_tpm(self, dt_start: datetime, dt_end: datetime, filters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves transactions per minute statistics.
        
        Args:
            dt_start (datetime): Start time
            dt_end (datetime): End time
            filters (Optional[List[Dict[str, Any]]]): Additional filters
            
        Returns:
            List[Dict[str, Any]]: List of TPM statistics
            
        Raises:
            PyMongoError: If an error occurs during the aggregation operation
        """
        try:
            query = [
                {
                    "$match": {
                        "logtime": {
                            "$gte": dt_start,
                            "$lt": dt_end,
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$logtime"},
                            "month": {"$month": "$logtime"},
                            "day": {"$dayOfMonth": "$logtime"},
                            "hour": {"$hour": "$logtime"},
                            "minute": {"$minute": "$logtime"},
                        },
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
            if filters:
                filters = self.translate_filters(filters)
                for f in filters:
                    query[0]["$match"].update(f)
            logger.debug(query)
            rs = self.collection.aggregate(query)
            return list(rs)
        except Exception as e:
            logger.error(f"Error retrieving TPM statistics: {str(e)}")
            raise
    def translate_filters(self, filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translates filters to MongoDB query format.
        
        Args:
            filters (List[Dict[str, Any]]): List of filters 
        """
        for f in filters:
            if "service.name" in f:
                dao = ServiceDao()
                service = dao.get_by_name(f.pop("service.name"))
                f.update({"service_id": ObjectId(service["_id"])})
        return filters
    
    def get_last_n_minutes(self, minutes: int, sensor_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves transactions from the last N minutes for specific sensors.
        
        Args:
            minutes (int): Number of minutes to look back
            sensor_ids (Optional[List[str]]): List of sensor IDs to filter by
            
        Returns:
            List[Dict[str, Any]]: List of transaction documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            dt_start = replace_tz((datetime.now() - timedelta(minutes=minutes)))
            query = {
                "logtime": {"$gte": dt_start},
                "sensor_id": {"$in": [ObjectId(id_str) for id_str in sensor_ids]},
            }
            logger.debug(query)
            rows = list(self.collection.find(query))
            for e in rows:
                 self._to_dict(e)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving last N minutes transactions: {str(e)}")
            raise

    def get_all(self, pagination: Optional[Dict[str, Any]] = None, 
                dt_start: Optional[datetime] = None, 
                dt_end: Optional[datetime] = None, 
                filters: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Retrieves all transactions with optional filtering and pagination.
        
        Args:
            pagination (Optional[Dict[str, Any]]): Pagination parameters
            dt_start (Optional[datetime]): Start date filter
            dt_end (Optional[datetime]): End date filter
            filters (Optional[List[Dict[str, Any]]]): Additional filters
            
        Returns:
            Dict[str, Any]: Dictionary with metadata and data
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = [
                {"$match": {}},
                {"$sort": {"logtime": -1}},
            ]
            if dt_start and dt_end:
                query[0]["$match"].update({"logtime": {"$gte": dt_start, "$lte": dt_end}})

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
                filters = self.translate_filters(filters)
                for f in filters:
                    query[0]["$match"].update(f)

            logger.debug(query)
            rs = list(self.collection.aggregate(query))[0]
            return self._fetch_all(rs, pagination=pagination)
        except Exception as e:
            logger.error(f"Error retrieving all transactions: {str(e)}")
            raise
