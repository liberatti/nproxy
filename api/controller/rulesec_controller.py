from typing import Dict, List, Optional, Union

from flask import Blueprint, Response

from common_utils import ResponseBuilder, has_any_authority
from model.seclang_model import RuleDao

routes = Blueprint("rulesec", __name__)


@routes.route("/by_code/<rule_code>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(rule_code: str) -> Response:
    """
    Retrieve a security rule by its code.
    
    Args:
        rule_code: The unique code identifier of the security rule
        
    Returns:
        Response: JSON response containing the security rule data or 404 error
    """
    dao = RuleDao()
    vo = dao.get_by_code(rule_code)
    return ResponseBuilder.data(vo) if vo else ResponseBuilder.error_404()
