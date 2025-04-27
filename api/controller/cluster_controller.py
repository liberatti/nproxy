import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from flask import Blueprint, request, send_file, Response
from marshmallow import ValidationError

from common_utils import (
    ResponseBuilder,
    has_any_authority,
    print_request,
    has_integration_key,
    socketio,
)
from model.config_model import ChangeDao, ConfigDao
from model.rbl_model import RBLDao
from model.transaction_model import TransactionDao
from model.upstream_model import NodeStatusDao
from tools.acme_tool import AcmeTool
from tools.cluster_tool import ClusterTool
from tools.feed_tool import SecurityFeedTool
from tools.mongo_tool import MongoTool

routes = Blueprint("cluster", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after cluster modifications.
    
    Args:
        response: The Flask response object
        
    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [200, 201]:
        dao = ChangeDao()
        if not dao.get_by_name("config"):
            dao.persist({"name": "config"})
        socketio.emit("tracking_evt")
    return response


@routes.route("/backup", methods=["POST"])
@has_any_authority(["superuser"])
def restore() -> Response:
    """
    Restore cluster configuration from a backup file.
    
    Returns:
        Response: Success message or error response
    """
    if "zipfile" not in request.files:
        print_request(request)
        return ResponseBuilder.error_500("No file uploaded")

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
            return ResponseBuilder.error_500("Failed processing restore", str(e))
    return ResponseBuilder.error_500("Invalid file format")


@routes.route("/backup", methods=["GET"])
@has_any_authority(["superuser"])
def backup() -> Response:
    """
    Create a backup of the cluster configuration.
    
    Returns:
        Response: Backup file download or error response
    """
    file_name = MongoTool.backup()
    return send_file(file_name, as_attachment=True)


@routes.route("/nodes", methods=["GET"])
def get_node_status() -> Response:
    """
    Retrieve the status of all cluster nodes including health and telemetry data.
    
    Returns:
        Response: JSON response containing node status information or 404 error
    """
    dao = NodeStatusDao()
    trn_dao = TransactionDao()
    result = dao.get_all()

    cut_date = datetime.now() - timedelta(minutes=1)
    if result["metadata"]["total_elements"] > 0:
        for node in result["data"]:
            # Update online status
            node["online"] = "last_check" in node and cut_date < node["last_check"]
            
            # Update health status
            if node["upstreams"]:
                node["healthy"] = True
                for upstream in node["upstreams"]:
                    for target in upstream["targets"]:
                        if not target["healthy"]:
                            upstream["healthy"] = False
                            node["healthy"] = False
                            break
            else:
                node["healthy"] = False

            # Update telemetry data
            telemetry = trn_dao.get_node_bandwidth(node["name"])
            node.update({
                "net_recv": telemetry[0]["net_recv"] if telemetry else 0,
                "net_send": telemetry[0]["net_send"] if telemetry else 0
            })
        return ResponseBuilder.data(result, dao.pageSchema)
    return ResponseBuilder.error_404()


@routes.route("/config", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get_config() -> Response:
    """
    Retrieve the active cluster configuration.
    
    Returns:
        Response: JSON response containing the configuration or 404 error
    """
    dao = ConfigDao()
    conf = dao.get_active()
    return ResponseBuilder.data(conf, dao.schema) if conf else ResponseBuilder.error_404()


@routes.route("/config", methods=["PUT"])
@has_any_authority(["superuser"])
def save() -> Response:
    """
    Update the cluster configuration.
    
    Returns:
        Response: JSON response containing the updated configuration or error message
    """
    dao = ConfigDao()
    try:
        vo = dao.json_load(request.json)
        dao.update_by_id(vo["_id"], vo)
        return ResponseBuilder.data(vo, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/changes", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def config_changes() -> Response:
    """
    Retrieve all configuration changes.
    
    Returns:
        Response: JSON response containing configuration changes or 404 error
    """
    dao = ChangeDao()
    result = dao.get_all()
    return ResponseBuilder.data(result) if result["metadata"]["total_elements"] > 0 else ResponseBuilder.error_404()


@routes.route("/apply", methods=["GET"])
@has_any_authority(["superuser"])
def apply() -> Response:
    """
    Apply pending configuration changes and handle certificate auto-renewal.
    
    Returns:
        Response: Success message or error response
    """
    dao = ChangeDao()
    changes = dao.get_all()
    action_result = ClusterTool.apply_config(reconfigure=True)
    
    if action_result["succeed"]:
        renewed_certs = AcmeTool.auto_renew()
        if renewed_certs > 0:
            action_result = ClusterTool.apply_config(reconfigure=True)
        
        if action_result["succeed"]:
            for change in changes["data"]:
                dao.delete_by_id(change["_id"])
            socketio.emit("tracking_aply")
            return ResponseBuilder.data(action_result)
    
    return ResponseBuilder.error_500(action_result["message"])


@routes.route("/geoip_info/<ipaddr>", methods=["GET"])
@has_integration_key()
def geoip_info(ipaddr: str) -> Response:
    """
    Retrieve GeoIP information for a given IP address.
    
    Args:
        ipaddr: The IP address to look up
        
    Returns:
        Response: JSON response containing GeoIP information or error response
    """
    if not ClusterTool.CONFIG:
        return ResponseBuilder.error_500("System not ready")
    
    info = SecurityFeedTool.geo_info(ipaddr)
    return ResponseBuilder.data(info)


@routes.route("/rbl/blocked/<sensor_id>/<ipaddr>", methods=["GET"])
@has_integration_key()
def rbl_status(ipaddr: str, sensor_id: str) -> Response:
    """
    Check if an IP address is blocked by RBL for a specific sensor.
    
    Args:
        ipaddr: The IP address to check
        sensor_id: The ID of the sensor to check against
        
    Returns:
        Response: JSON response containing RBL check results or error response
    """
    if not ClusterTool.CONFIG:
        return ResponseBuilder.error_500("System not ready")
    
    for sensor in ClusterTool.CONFIG["sensors"]:
        if sensor["_id"] == sensor_id:
            model = RBLDao()
            rbl_result = model.check_by_ip(ipaddr, sensor)
            return ResponseBuilder.data(rbl_result)
    
    return ResponseBuilder.error_500("Failed checking RBL")
