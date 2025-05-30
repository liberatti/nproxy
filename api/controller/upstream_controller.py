import json

from flask import Blueprint, request
from marshmallow import ValidationError

from model.service_model import ServiceDao
from common_utils import ResponseBuilder, has_any_authority, get_pagination
from common_utils import socketio
from model.config_model import ChangeDao
from model.upstream_model import UpstreamDao

routes = Blueprint("upstream", __name__)

@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE", "PATCH"] and  response.status_code in [200,201]:
        dao = ChangeDao()
        if not dao.get_by_name("upstream"):
            dao.persist({"name": "upstream"})
        socketio.emit('tracking_evt')
    return response


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    dao = UpstreamDao()
    result = dao.get_all(pagination=get_pagination())
    if result["metadata"]["total_elements"] > 0:
        for e in result['data']:
            if 'content' in e:
                e.pop('content')
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()

@routes.route("/<upstream_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(upstream_id):
    dao = UpstreamDao()
    upstream = dao.get_by_id(upstream_id)
    if upstream:
        if 'content' in upstream:
            upstream.pop('content')
        return ResponseBuilder.data(upstream, dao.schema)
    else:
        return ResponseBuilder.error_404()

@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save():
    dao = UpstreamDao()
    try:
        if request.content_type.startswith('multipart/form-data'):
            metadata = request.files.get('metadata')
            upstream = json.load(metadata.stream)
            file = request.files.get('zipfile')
            if file:
                upstream.update({
                    "content": file.read()
                })
        else:
            upstream = dao.json_load(request.json)
        dao.persist(upstream)
        if 'content' in upstream:
            upstream.pop("content")
        return ResponseBuilder.data(upstream, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)

@routes.route("/<upstream_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(upstream_id):
    dao = UpstreamDao()
    try:
        if request.content_type.startswith('multipart/form-data'):
            metadata = request.files.get('metadata')
            upstream = json.load(metadata.stream)
            file = request.files.get('zipfile')
            if file:
                upstream.update({
                    "content": file.read()
                })
        else:
            upstream = dao.json_load(request.json)
        dao.update_by_id(upstream_id, upstream)
        if 'content' in upstream:
            upstream.pop("content")
        return ResponseBuilder.data(upstream, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)

@routes.route("/<upstream_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(upstream_id):
    dao = UpstreamDao()
    service_dao = ServiceDao()
    service_list = service_dao.get_all()
    if "data" in service_list:
        for service in service_list["data"]:
            if "routes" in service:
                for route in service["routes"]:
                    if upstream_id in route["upstream"]["_id"]:
                        return ResponseBuilder.error_500("Upstream in use")
    r = dao.delete_by_id(upstream_id)
    if r:
        return ResponseBuilder.data_removed(upstream_id)
    else:
        return ResponseBuilder.error_404()