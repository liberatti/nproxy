from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, has_any_authority, get_pagination
from api.common_utils import socketio
from api.model.config_model import ChangeDao
from api.model.service_model import RouteFilterDao

routes = Blueprint("route_filter", __name__)

@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE"] and  response.status_code in [200,201]:
        dao = ChangeDao()
        if not dao.get_by_name("route_filter"):
            dao.persist({"name": "route_filter"})
        socketio.emit('tracking_evt')
    return response

@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    dao = RouteFilterDao()
    result = dao.get_all(pagination=get_pagination())
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<route_filter_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(route_filter_id):
    dao = RouteFilterDao()
    route_filter = dao.get_by_id(route_filter_id)
    if route_filter:
        return ResponseBuilder.data(route_filter, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
    dao = RouteFilterDao()
    try:
        route_filter = dao.json_load(request.json)
        dao.persist(route_filter)
        return ResponseBuilder.data(route_filter, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<route_filter_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(route_filter_id):
    dao = RouteFilterDao()
    try:
        route_filter = dao.json_load(request.json)
        dao.update_by_id(route_filter_id, route_filter)
        return ResponseBuilder.data(route_filter, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<route_filter_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(route_filter_id):
    dao = RouteFilterDao()
    r = dao.delete_by_id(route_filter_id)
    if r:
        return ResponseBuilder.data_removed(route_filter_id)
    else:
        return ResponseBuilder.error_404()
