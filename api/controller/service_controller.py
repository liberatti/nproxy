from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, has_any_authority, get_pagination, deep_merge
from api.common_utils import socketio
from api.model.config_model import ChangeDao
from api.model.service_model import ServiceDao

routes = Blueprint("service", __name__)

@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE", "PATCH"] and  response.status_code in [200,201]:
        dao = ChangeDao()
        if not dao.get_by_name("service"):
            dao.persist({"name": "service"})
        socketio.emit('tracking_evt')
    return response

@routes.route("/<service_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(service_id):
    dao = ServiceDao()
    service = dao.get_by_id(service_id)
    if service:
        return ResponseBuilder.data(service, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
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
@has_any_authority(["viewer", "superuser"])
def search():
    dao = ServiceDao()
    result = dao.get_all(pagination=get_pagination())
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<service_id>", methods=["PATCH"])
@has_any_authority(["superuser"])
def partial_update(service_id):
    dao = ServiceDao()
    try:
        service_new = dao.json_load(request.json)
        service_old = dao.get_by_id(service_id)

        dao.update_by_id(service_id, deep_merge(service_old, service_new))
        return ResponseBuilder.ok("Partially updated")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<service_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(service_id):
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
@has_any_authority(["superuser"])
def delete(service_id):
    dao = ServiceDao()
    result = dao.delete_by_id(service_id)
    if result:
        return ResponseBuilder.data_removed(service_id)
    else:
        return ResponseBuilder.error_404()
