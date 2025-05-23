import os
from datetime import datetime, timedelta

from flask import Blueprint, request, send_file
from marshmallow import ValidationError

from api.common_utils import (
    ResponseBuilder,
    has_any_authority,
    print_request,
    has_integration_key,
    socketio,
)
from api.model.config_model import ChangeDao, ConfigDao
from api.model.rbl_model import RBLDao
from api.model.transaction_model import TransactionDao
from api.model.upstream_model import NodeStatusDao
from api.tools.acme_tool import AcmeTool
from api.tools.cluster_tool import ClusterTool
from api.tools.feed_tool import SecurityFeedTool
from api.tools.mongo_tool import MongoTool

routes = Blueprint("cluster", __name__)


@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [
        200,
        201,
    ]:
        dao = ChangeDao()
        if not dao.get_by_name("config"):
            dao.persist({"name": "config"})
        socketio.emit("tracking_evt")
    return response


@routes.route("/backup", methods=["POST"])
@has_any_authority(["superuser"])
def restore():
    if "zipfile" not in request.files:
        print_request(request)
        return ResponseBuilder.error_500("Not file uploaded")

    file = request.files["zipfile"]
    if file and file.filename.endswith(".zip"):
        try:
            zip_path = os.path.join("/tmp", file.filename)
            file.save(zip_path)
            MongoTool.restore(zip_path)
            dao = ChangeDao()
            if not dao.get_by_name("backup"):
                dao.persist({"name": "backup"})
            return ResponseBuilder.ok("ok")
        except Exception as e:
            return ResponseBuilder.error_500("Failed processing restore", e)


@routes.route("/backup", methods=["GET"])
@has_any_authority(["superuser"])
def backup():
    file_name = MongoTool.backup()
    return send_file(file_name, as_attachment=True)


@routes.route("/nodes", methods=["GET"])
# @has_any_authority(["viewer", "superuser"])
def get_node_status():
    dao = NodeStatusDao()
    trn_dao = TransactionDao()
    result = dao.get_all()

    cut_date = datetime.now() - timedelta(minutes=1)
    if result["metadata"]["total_elements"] > 0:
        for n in result["data"]:
            n.update({"online": ("last_check" in n and cut_date < n["last_check"])})
            if len(n["upstreams"]) > 0:
                n.update({"healthy": True})
                for u in n["upstreams"]:
                    for s in u["targets"]:
                        if not s["healthy"]:
                            u.update({"healthy": False})
                            n.update({"healthy": False})
                            break
            else:
                n.update({"healthy": False})

            telemetry = trn_dao.get_node_bandwidth(n["name"])
            if telemetry:
                n.update(
                    {
                        "net_recv": telemetry[0]["net_recv"],
                        "net_send": telemetry[0]["net_send"],
                    }
                )
            else:
                n.update({"net_recv": 0, "net_send": 0})
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/config", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get_config():
    dao = ConfigDao()
    conf = dao.get_active()
    if conf:
        return ResponseBuilder.data(conf, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/config", methods=["PUT"])
@has_any_authority(["superuser"])
def save():
    dao = ConfigDao()
    try:
        vo = dao.json_load(request.json)
        dao.update_by_id(vo["_id"], vo)
        return ResponseBuilder.data(vo, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/changes", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def config_changes():
    dao = ChangeDao()
    result = dao.get_all()
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result)
    else:
        return ResponseBuilder.error_404()


@routes.route("/apply", methods=["GET"])
@has_any_authority(["superuser"])
def apply():
    dao = ChangeDao()
    changes = dao.get_all()
    action_result = ClusterTool.apply_config(reconfigure=True)
    if action_result["succeed"]:
        c = AcmeTool.auto_renew()
        if c > 0:
            action_result = ClusterTool.apply_config(reconfigure=True)
        if action_result["succeed"]:
            for c in changes["data"]:
                dao.delete_by_id(c["_id"])

        socketio.emit("tracking_aply")
        return ResponseBuilder.data(action_result)
    else:
        return ResponseBuilder.error_500(action_result["message"])


@routes.route("/geoip_info/<ipaddr>", methods=["GET"])
@has_integration_key()
def geoip_info(ipaddr):
    if ClusterTool.CONFIG:
        info = SecurityFeedTool.geo_info(ipaddr)
        return ResponseBuilder.data(info)
    else:
        return ResponseBuilder.error_500("System not ready")


@routes.route("/rbl/blocked/<sensor_id>/<ipaddr>", methods=["GET"])
@has_integration_key()
def rbl_status(ipaddr, sensor_id):
    if ClusterTool.CONFIG:
        for s in ClusterTool.CONFIG["sensors"]:
            if s["_id"] == sensor_id:
                model = RBLDao()
                rbl_result = model.check_by_ip(ipaddr, s)
                return ResponseBuilder.data(rbl_result)
        return ResponseBuilder.error_500("Failed cheking RBL")
    else:
        return ResponseBuilder.error_500("System not ready")
