from flask import Blueprint, Response

from common_utils import ResponseBuilder
from model.upstream_model import NodeStatusSchema
from tools.cluster_tool import ClusterTool

routes = Blueprint("health", __name__)


@routes.route("/", methods=["GET"])
def get_config() -> Response:
    """
    Retrieve the health status of the node.
    
    Returns:
        Response: JSON response containing the node health status information
    """
    return ResponseBuilder.data(ClusterTool.node_monitor(), NodeStatusSchema())
