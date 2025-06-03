from flask import Blueprint, request, Response
from marshmallow import ValidationError

from common_utils import (
    ResponseBuilder,
    has_any_authority,
    get_pagination,
    deep_merge,
    socketio,
)
from model.config_model import ChangeDao
from model.service_model import ServiceDao

routes = Blueprint("service", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after service modifications.
    
    Args:
        response: The Flask response object
        
    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE", "PATCH"] and response.status_code in [200, 201]:
        dao = ChangeDao()
        if not dao.get_by_name("service"):
            dao.persist({"name": "service"})
        socketio.emit('tracking_evt')
    return response


@routes.route("/<service_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(service_id: str) -> Response:
    """
    Retrieve a specific service by ID.
    
    Args:
        service_id: The unique identifier of the service
        
    Returns:
        Response: JSON response containing the service data or 404 error
    """
    dao = ServiceDao()
    service = dao.get_by_id(service_id)
    return ResponseBuilder.data(service, dao.schema) if service else ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new service.
    Checks if the domains (SANS) are already in use before creating.
    
    Returns:
        Response: JSON response containing the created service or error message
    """
    dao = ServiceDao()
    try:
        service_dict = dao.json_load(request.json)
        sv_check = dao.get_by_sans(service_dict['sans'])
        if sv_check:
            return ResponseBuilder.error('Domains in use', code=406)

        pk = dao.persist(service_dict)
        service = dao.get_by_id(pk)
        return ResponseBuilder.data(service, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all services.
    
    Returns:
        Response: JSON response containing paginated service list or 404 error
    """
    dao = ServiceDao()
    result = dao.get_all(pagination=get_pagination())
    return ResponseBuilder.data(result, dao.pageSchema) if result["metadata"]["total_elements"] > 0 else ResponseBuilder.error_404()


@routes.route("/<service_id>", methods=["PATCH"])
@has_any_authority(authorities=["superuser"])
def partial_update(service_id: str) -> Response:
    """
    Partially update a service with specific fields.
    
    Args:
        service_id: The unique identifier of the service to update
        
    Returns:
        Response: Success message or error response
    """
    dao = ServiceDao()
    try:
        service_new = dao.json_load(request.json)
        service_old = dao.get_by_id(service_id)
        dao.update_by_id(service_id, deep_merge(service_old, service_new))
        return ResponseBuilder.ok("Partially updated")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<service_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(service_id: str) -> Response:
    """
    Update an existing service.
    Checks if the domains (SANS) are already in use before updating.
    
    Args:
        service_id: The unique identifier of the service to update
        
    Returns:
        Response: JSON response containing the updated service or error message
    """
    dao = ServiceDao()
    try:
        service_dict = dao.json_load(request.json)
        sv_check = dao.get_by_sans(service_dict['sans'])
        if sv_check and service_id not in sv_check['_id']:
            return ResponseBuilder.error('Domains in use', code=406)
            
        dao.update_by_id(service_id, service_dict)
        return ResponseBuilder.data(dao.get_by_id(service_id), dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<service_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(service_id: str) -> Response:
    """
    Delete a service.
    
    Args:
        service_id: The unique identifier of the service to delete
        
    Returns:
        Response: Success message or error response
    """
    dao = ServiceDao()
    result = dao.delete_by_id(service_id)
    return ResponseBuilder.data_removed(service_id) if result else ResponseBuilder.error_404()
