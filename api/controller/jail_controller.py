from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, has_any_authority, get_pagination
from api.common_utils import socketio
from api.model.config_model import ChangeDao
from api.model.jail_model import JailDao

routes = Blueprint("jail", __name__)


@routes.before_request
def before():
    if request.method in ["PUT", "POST", "DELETE"]:
        dao = ChangeDao()
        if not dao.get_by_name("jail"):
            dao.persist({"name": "jail"})
        socketio.emit('tracking_evt')


@routes.route("/<jail_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(jail_id):
    dao = JailDao()
    jail = dao.get_by_id(jail_id)
    if jail:
        return ResponseBuilder.data(jail, schema=dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
    dao = JailDao()
    try:
        jail_dict = dao.json_load(request.json)
        pk = dao.persist(jail_dict)
        jail = dao.get_by_id(pk)
        return ResponseBuilder.data(jail, schema=dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    dao = JailDao()
    result = dao.get_all(pagination=get_pagination())

    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, schema=dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<jail_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(jail_id):
    dao = JailDao()
    try:
        jail_dict = dao.json_load(request.json)
        result = dao.update_by_id(jail_id, jail_dict)

        return ResponseBuilder.data(result, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<jail_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(jail_id):
    dao = JailDao()
    result = dao.delete_by_id(jail_id)
    if result:
        return ResponseBuilder.data_removed(jail_id)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<jail_id>/add/<addr>", methods=["PUT"])
@has_any_authority(["superuser"])
def add_to_jail(jail_id, addr):
    dao = JailDao()
    try:
        result = dao.get_by_id(jail_id)
        result["content"].append({"ipaddr": addr})
        dao.update_by_id(jail_id, result)
        return ResponseBuilder.ok("ok")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<jail_id>/del/<addr>", methods=["PUT"])
@has_any_authority(["superuser"])
def del_to_jail(jail_id, addr):
    dao = JailDao()
    try:
        result = dao.get_by_id(jail_id)
        t_arr = []
        for c in result["content"]:
            if addr not in c["ipaddr"]:
                t_arr.append(c)
        result["content"] = t_arr
        dao.update_by_id(jail_id, result)
        return ResponseBuilder.ok("ok")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)
