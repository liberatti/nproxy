from typing import Dict, List, Optional, Union

from flask import Blueprint, request, Response
from marshmallow import ValidationError

from common_utils import (
    ResponseBuilder,
    has_any_authority,
    get_pagination,
    socketio,
)
from model.config_model import ChangeDao
from model.service_model import RouteFilterDao

routes = Blueprint("route_filter", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after route filter modifications.
    
    Args:
        response: The Flask response object
        
    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [200, 201]:
        dao = ChangeDao()
        if not dao.get_by_name("route_filter"):
            dao.persist({"name": "route_filter"})
        socketio.emit('tracking_evt')
    return response


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all route filters.
    
    Returns:
        Response: JSON response containing paginated route filter list or 404 error
    """
    dao = RouteFilterDao()
    result = dao.get_all(pagination=get_pagination())
    return ResponseBuilder.data(result, dao.pageSchema) if result["metadata"]["total_elements"] > 0 else ResponseBuilder.error_404()


@routes.route("/<route_filter_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(route_filter_id: str) -> Response:
    """
    Retrieve a specific route filter by ID.
    
    Args:
        route_filter_id: The unique identifier of the route filter
        
    Returns:
        Response: JSON response containing the route filter data or 404 error
    """
    dao = RouteFilterDao()
    route_filter = dao.get_by_id(route_filter_id)
    return ResponseBuilder.data(route_filter, dao.schema) if route_filter else ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new route filter.
    
    Returns:
        Response: JSON response containing the created route filter or error message
    """
    dao = RouteFilterDao()
    try:
        route_filter = dao.json_load(request.json)
        dao.persist(route_filter)
        return ResponseBuilder.data(route_filter, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<route_filter_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(route_filter_id: str) -> Response:
    """
    Update an existing route filter.
    
    Args:
        route_filter_id: The unique identifier of the route filter to update
        
    Returns:
        Response: JSON response containing the updated route filter or error message
    """
    dao = RouteFilterDao()
    try:
        route_filter = dao.json_load(request.json)
        dao.update_by_id(route_filter_id, route_filter)
        return ResponseBuilder.data(route_filter, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<route_filter_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(route_filter_id: str) -> Response:
    """
    Delete a route filter.
    
    Args:
        route_filter_id: The unique identifier of the route filter to delete
        
    Returns:
        Response: Success message or error response
    """
    dao = RouteFilterDao()
    result = dao.delete_by_id(route_filter_id)
    return ResponseBuilder.data_removed(route_filter_id) if result else ResponseBuilder.error_404()
