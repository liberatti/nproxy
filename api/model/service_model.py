from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.certificate_model import CertificateDao, CertificateSchema
from model.mongo_base_model import MongoDAO
from model.sensor_model import SensorSchema, SensorDao
from model.upstream_model import UpstreamDao, UpstreamSchema


class HeaderSchema(Schema):
    """
    Schema for HTTP header validation and serialization.
    
    This schema defines the structure and validation rules for HTTP headers.
    """
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    content = fields.String()


class BindSchema(Schema):
    """
    Schema for service binding validation and serialization.
    
    This schema defines the structure and validation rules for service bindings.
    """
    class Meta:
        unknown = EXCLUDE

    port = fields.Integer()
    protocol = fields.String()
    ssl_upgrade = fields.Boolean()


class RedirectSchema(Schema):
    """
    Schema for redirect validation and serialization.
    
    This schema defines the structure and validation rules for redirects.
    """
    class Meta:
        unknown = EXCLUDE

    code = fields.Integer()
    url = fields.String()


class RouteFilterSchema(Schema):
    """
    Schema for route filter validation and serialization.
    
    This schema defines the structure and validation rules for route filters.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    description = fields.String()
    type = fields.String()  # SSL_CLIENT_AUTH, LDAP_AUTH
    ssl_dn_regex = fields.String()
    ssl_fingerprints = fields.List(fields.String())
    ldap_host = fields.String()
    ldap_base_dn = fields.String()
    ldap_bind_dn = fields.String()
    ldap_bind_password = fields.String()
    ldap_group_dn = fields.String()


class RouteSchema(Schema):
    """
    Schema for route validation and serialization.
    
    This schema defines the structure and validation rules for routes.
    """
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    type = fields.String()
    paths = fields.List(fields.String())
    methods = fields.List(fields.String())
    upstream = fields.Nested(UpstreamSchema)
    redirect = fields.Nested(RedirectSchema)
    sensor = fields.Nested(SensorSchema)
    monitor_only = fields.Boolean()
    cache_methods = fields.List(fields.String())
    filters = fields.Nested(RouteFilterSchema, many=True)


class ServiceSchema(Schema):
    """
    Schema for service validation and serialization.
    
    This schema defines the structure and validation rules for services.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    body_limit = fields.Integer()
    timeout = fields.Integer()
    active = fields.Boolean()
    buffer = fields.Integer()
    bindings = fields.Nested(BindSchema, many=True)
    headers = fields.Nested(HeaderSchema, many=True)
    routes = fields.Nested(RouteSchema, many=True)
    compression = fields.Boolean()
    compression_types = fields.List(fields.String())
    rate_limit = fields.Boolean()
    rate_limit_per_sec = fields.Integer()
    sans = fields.List(fields.String())
    ssl_protocols = fields.List(fields.String())
    certificate = fields.Nested(CertificateSchema)
    ssl_client_ca = fields.String()
    ssl_client_auth = fields.Boolean(load_default=False, dump_default=False)


class RouteFilterDao(MongoDAO):
    """
    DAO for managing route filters.
    
    This class extends MongoDAO to provide specific operations
    related to route filter management.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'route_filters' collection and schema.
        """
        super().__init__("route_filters", schema=RouteFilterSchema)


class ServiceDao(MongoDAO):
    """
    DAO for managing services.
    
    This class extends MongoDAO to provide specific operations
    related to service management, including certificate and route handling.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'service' collection and schema.
        """
        super().__init__("service", schema=ServiceSchema)



    def _from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unloads a service document, converting nested objects to IDs.
        
        Args:
            vo (Dict[str, Any]): Service document to unload
            
        Returns:
            Dict[str, Any]: Unloaded service document
        """
        super()._from_dict(vo)

        if "certificate" in vo:
            certificate = vo.pop("certificate")
            if "certificate_id" not in certificate:
                vo.update({"certificate_id": ObjectId(certificate["_id"])})

        if "routes" in vo:
            for route in vo["routes"]:
                if "type" not in route or len(route["type"]) <= 0:
                    route.update({"type": "upstream"})

                if "filters" in route:
                    fs_ids = []
                    for b in route.pop("filters"):
                        fs_ids.append(ObjectId(b["_id"]))
                    route.update({"filter_ids": fs_ids})

                if "upstream" in route["type"]:
                    upstream = route.pop("upstream")
                    route.update({"upstream_id": ObjectId(upstream["_id"])})

                if "sensor" in route:
                    sensor = route.pop("sensor")
                    route.update({"sensor_id": ObjectId(sensor["_id"])})
        return vo

    def _to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Loads a service document with its associated resources.
        
        Args:
            vo (Optional[Dict[str, Any]]): Service document to load
            
        Returns:
            Optional[Dict[str, Any]]: Loaded service document
        """
        super()._to_dict(vo)

        if "certificate_id" in vo:
            crt_id = vo.pop("certificate_id")
            vo.update({"certificate": CertificateDao().get_by_id(ObjectId(crt_id))})

        if "routes" in vo:
            for route in vo["routes"]:
                if "type" not in route:  # default value for compatibility
                    route.update({"type": "upstream"})

                if "filter_ids" in route:
                    fs = []
                    dao = RouteFilterDao()
                    for b in route.pop("filter_ids"):
                        fs.append(dao.get_by_id(str(b)))
                    route.update({"filters": fs})

                if "upstream" in route["type"]:
                    upstream_id = route.pop("upstream_id")
                    ups_dao = UpstreamDao()
                    route.update({"upstream": ups_dao.get_descr_by_id(upstream_id)})

                if "sensor_id" in route:
                    sensor_id = route.pop("sensor_id")
                    sen_dao = SensorDao()
                    route.update({"sensor": sen_dao.get_descr_by_id(sensor_id)})
        return vo

    def get_by_sans(self, sans: List[str], active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a service by its SANs (Subject Alternative Names).
        
        Args:
            sans (List[str]): List of SANs to search for
            active (Optional[bool]): Filter by active status
            
        Returns:
            Optional[Dict[str, Any]]: Service document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"sans": {"$in": sans}}
            if active is not None:
                query["$and"].append({"active": {"$eq": active}})

            logger.debug(query)
            vo = self.collection.find_one(query)
            if vo:
                 self._to_dict(vo)
            return vo
        except Exception as e:
            logger.error(f"Error retrieving service by SANs: {str(e)}")
            raise

    def get_all_for_renew(self, ssl_provider: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves all services that need certificate renewal.
        
        Args:
            ssl_provider (List[str]): List of SSL providers to check
            
        Returns:
            List[Dict[str, Any]]: List of service documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"provider": {"$in": ssl_provider}}
            logger.debug(query)
            rows = list(self.collection.find(query))
            for e in rows:
                 self._to_dict(e)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving services for renewal: {str(e)}")
            raise

    def getall_by_certificate_id(self, certificate_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all active services using a specific certificate.
        
        Args:
            certificate_id (str): Certificate ID to search for
            
        Returns:
            List[Dict[str, Any]]: List of service documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"certificate_id": ObjectId(certificate_id), "active": True}
            logger.debug(query)
            rows = list(self.collection.find(query))
            for e in rows:
                 self._to_dict(e)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving services by certificate: {str(e)}")
            raise
