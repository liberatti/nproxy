from flask import Blueprint

from api.common_utils import ResponseBuilder
from api.model.upstream_model import NodeStatusSchema
from api.tools.cluster_tool import ClusterTool

routes = Blueprint("health", __name__)


@routes.route("/", methods=["GET"])
def get_config():
    return ResponseBuilder.data(ClusterTool.node_monitor(),NodeStatusSchema())
