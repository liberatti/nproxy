from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import (
    ResponseBuilder,
    has_any_authority,
    get_pagination,
    has_integration_key,
    socketio,
)
from api.model.config_model import ChangeDao
from api.model.sensor_model import SensorDao
from api.tools.cluster_tool import ClusterTool
from api.tools.feed_tool import SecurityFeedTool

routes = Blueprint("sensor", __name__)


@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [
        200,
        201,
    ]:
        dao = ChangeDao()
        if not dao.get_by_name("sensor"):
            dao.persist({"name": "sensor"})
        socketio.emit("tracking_evt")
    return response


@routes.route("/<sensor_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(sensor_id):
    dao = SensorDao()
    sensor = dao.get_by_id(sensor_id)
    if sensor:
        return ResponseBuilder.data(sensor, schema=dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
    dao = SensorDao()
    try:
        sensor_dict = dao.json_load(request.json)
        pk = dao.persist(sensor_dict)
        sensor = dao.get_by_id(pk)
        return ResponseBuilder.data(sensor, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    dao = SensorDao()
    result = dao.get_all(pagination=get_pagination())
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<sensor_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(sensor_id):
    dao = SensorDao()
    try:
        sensor_dict = dao.json_load(request.json)
        r = dao.update_by_id(sensor_id, sensor_dict)
        return ResponseBuilder.data(r, schema=dao.schema)

    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<sensor_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(sensor_id):
    dao = SensorDao()
    result = dao.delete_by_id(sensor_id)
    if result:
        return ResponseBuilder.data_removed(sensor_id)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<sensor_id>/check/<ipaddr>", methods=["GET"])
@has_integration_key()
def geoip_info(ipaddr):
    if ClusterTool.CONFIG:
        geo = SecurityFeedTool.geo_info(ipaddr)
        ip_info = {"country": geo["country"]}

        return ResponseBuilder.data(ip_info)
    else:
        return ResponseBuilder.error_500("System not ready")
