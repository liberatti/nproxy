from typing import Dict, List, Optional, Union

from flask import Blueprint, Response

from common_utils import (
    ResponseBuilder,
    has_any_authority
)
from tools.cluster_tool import ClusterTool

routes = Blueprint("replica", __name__)


@routes.route("/scn", methods=["GET"])
@has_any_authority( _internal=True)
def scn() -> Response:
    """
    Retrieve the System Change Number (SCN) from the cluster configuration.
    
    Returns:
        Response: JSON response containing the SCN or error response
    """
    if not ClusterTool.CONFIG:
        return ResponseBuilder.error_500("System not ready")
    return ResponseBuilder.data({'scn': ClusterTool.CONFIG['scn']})


@routes.route("/config", methods=["GET"])
@has_any_authority(_internal=True)
def config() -> Response:
    """
    Retrieve the cluster configuration.
    
    Returns:
        Response: JSON response containing the cluster configuration
    """
    return ResponseBuilder.data(ClusterTool.CONFIG)