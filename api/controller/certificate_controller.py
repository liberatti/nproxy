from datetime import datetime
from typing import Dict, List, Optional, Union

from flask import Blueprint, request, Response
from marshmallow import ValidationError

from common_utils import (
    ResponseBuilder,
    deep_merge,
    has_any_authority,
    get_pagination,
    replace_tz,
    socketio
)
from model.certificate_model import CertificateDao
from model.config_model import ChangeDao
from model.service_model import ServiceDao
from tools.ssl_tool import SSLTool
from config import TZ

routes = Blueprint("certificate", __name__)

@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after certificate modifications.
    
    Args:
        response: The Flask response object
        
    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE", "PATCH"] and response.status_code in [200, 201]:
        dao = ChangeDao()
        if not dao.get_by_name("certificate"):
            dao.persist({"name": "certificate"})
        socketio.emit('tracking_evt')
    return response

@routes.route("/<certificate_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(certificate_id: str) -> Response:
    """
    Retrieve a specific certificate by ID.
    
    Args:
        certificate_id: The unique identifier of the certificate
        
    Returns:
        Response: JSON response containing the certificate data or 404 error
    """
    dao = CertificateDao()
    certificate = dao.get_by_id(certificate_id)
    return ResponseBuilder.data(certificate, schema=dao.schema) if certificate else ResponseBuilder.error_404()

@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all certificates with their current status.
    
    Returns:
        Response: JSON response containing paginated certificate list or 404 error
    """
    dao = CertificateDao()
    result = dao.get_all(pagination=get_pagination(), filters=[])

    if result and result["metadata"]["total_elements"] > 0:
        renew_date = replace_tz(datetime.now())
        for cert in result["data"]:
            cert["status"] = "EXPIRED" if cert["force_renew"] or replace_tz(cert["not_after"]) < renew_date else "VALID"
        return ResponseBuilder.data(result, schema=dao.pageSchema)
    return ResponseBuilder.error_404()

@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new certificate.
    Supports three types of certificates:
    - EXTERNAL: Import existing certificate
    - MANAGED: Create managed certificate
    - SELF: Create self-signed certificate
    
    Returns:
        Response: JSON response containing the created certificate or error message
    """
    dao = CertificateDao()
    try:
        dto = dao.json_load(request.json)
        pk = None
        
        # Handle EXTERNAL certificate
        if 'EXTERNAL' in dto['provider']:
            crt = SSLTool.crt_from_pem(dto["certificate"])
            dto.update(SSLTool.extract_info_from_crt(crt))
            dto.update({
                "status": "EXPIRED" if dto["not_after"] <= datetime.now(TZ) else "VALID",
                "force_renew": False
            })
            pk = dao.persist(dto)
        
        # Handle MANAGED or SELF certificates
        elif dto["provider"] in ["MANAGED", "SELF"]:
            self_crt = SSLTool.create_certificate("localhost")
            self_chain = [SSLTool.crt_to_pem(c) for c in self_crt["chain"]]
            crt = {
                "name": dto["name"],
                "chain": "\n".join(self_chain),
                "certificate": SSLTool.crt_to_pem(self_crt["certificate"]),
                "private_key": SSLTool.private_to_pem(self_crt["private_key"]),
                "subjects": self_crt["subjects"],
                "not_before": self_crt["not_before"],
                "not_after": self_crt["not_after"],
                "force_renew": True,
                "provider": dto["provider"]
            }
            pk = dao.persist(crt)

        certificate = dao.get_by_id(pk)
        return ResponseBuilder.data(certificate, schema=dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)

@routes.route("/<certificate_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(certificate_id: str) -> Response:
    """
    Update an existing certificate.
    
    Args:
        certificate_id: The unique identifier of the certificate to update
        
    Returns:
        Response: JSON response containing the updated certificate or error message
    """
    dao = CertificateDao()
    try:
        dto = dao.json_load(request.json)
        
        # Handle EXTERNAL certificate update
        if dto['provider'] in ['EXTERNAL']:
            crt = SSLTool.crt_from_pem(dto["certificate"])
            dto.update(SSLTool.extract_info_from_crt(crt))
            dto.update({
                "status": "EXPIRED" if dto["not_after"] <= datetime.now(TZ) else "VALID",
                "force_renew": True
            })
            dao.update_by_id(certificate_id, dto)
        
        # Handle MANAGED or SELF certificate update
        elif dto["provider"] in ["MANAGED", "SELF"]:
            self_crt = SSLTool.create_certificate("localhost")
            self_chain = [SSLTool.crt_to_pem(c) for c in self_crt["chain"]]
            crt = {
                "name": dto["name"],
                "chain": "\n".join(self_chain),
                "certificate": SSLTool.crt_to_pem(self_crt["certificate"]),
                "private_key": SSLTool.private_to_pem(self_crt["private_key"]),
                "subjects": self_crt["subjects"],
                "not_before": self_crt["not_before"],
                "not_after": self_crt["not_after"],
                "force_renew": True,
                "provider": dto["provider"]
            }
            dao.update_by_id(certificate_id, crt)
        
        return ResponseBuilder.data(dto, schema=dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)

@routes.route("/<certificate_id>", methods=["PATCH"])
@has_any_authority(authorities=["superuser"])
def partial_update(certificate_id: str) -> Response:
    """
    Partially update a certificate with specific fields.
    
    Args:
        certificate_id: The unique identifier of the certificate to update
        
    Returns:
        Response: Success message or error response
    """
    dao = CertificateDao()
    try:
        c_new = dao.json_load(request.json)
        c_old = dao.get_by_id(certificate_id)
        dao.update_by_id(certificate_id, deep_merge(c_old, c_new))
        return ResponseBuilder.ok("Certificate partially updated")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)
    except Exception as err:
        return ResponseBuilder.error(msg=str(err))

@routes.route("/<certificate_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(certificate_id: str) -> Response:
    """
    Delete a certificate if it's not in use by any service.
    
    Args:
        certificate_id: The unique identifier of the certificate to delete
        
    Returns:
        Response: Success message or error response
    """
    dao = CertificateDao()
    dao_service = ServiceDao()
    
    # Check if certificate is in use by any HTTPS service
    service_list = dao_service.get_all()
    if "data" in service_list:
        for service in service_list["data"]:
                if certificate_id in service["certificate"]["_id"]:
                    return ResponseBuilder.error_500("Certificate in use")
    result = dao.delete_by_id(certificate_id)
    return ResponseBuilder.data_removed(certificate_id) if result else ResponseBuilder.error_404()
