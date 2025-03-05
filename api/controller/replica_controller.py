from flask import Blueprint

from api.common_utils import (
    ResponseBuilder, has_integration_key, )
from api.tools.cluster_tool import ClusterTool

routes = Blueprint("replica", __name__)


@routes.route("/scn", methods=["GET"])
@has_integration_key()
def scn():
    if ClusterTool.CONFIG:
        return ResponseBuilder.data({'scn':ClusterTool.CONFIG['scn']})
    else: return ResponseBuilder.error_500("System not ready")

@routes.route("/config", methods=["GET"])
@has_integration_key()
def config():
    return ResponseBuilder.data(ClusterTool.CONFIG)