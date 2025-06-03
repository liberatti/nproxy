from typing import Dict, List, Optional, Union

from flask import Blueprint, request, Response

from common_utils import ResponseBuilder, has_any_authority
from model.seclang_model import RuleCategoryDao
from tools.ruleset_tool import RuleSetParser

routes = Blueprint("rulecat", __name__)


@routes.route("/<cat_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(cat_id: str) -> Response:
    """
    Retrieve a specific rule category by ID.
    
    Args:
        cat_id: The unique identifier of the rule category
        
    Returns:
        Response: JSON response containing the rule category data or 404 error
    """
    dao = RuleCategoryDao()
    cat = dao.get_by_id(cat_id)
    if not cat:
        return ResponseBuilder.error_404()
    return Response(
        RuleSetParser.dumps(cat),
        status=201,
        mimetype="application/json"
    )


@routes.route("/by_name/<cat_name>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get_by_name(cat_name: str) -> Response:
    """
    Retrieve a rule category by name.
    
    Args:
        cat_name: The name of the rule category
        
    Returns:
        Response: JSON response containing the rule category data or 404 error
    """
    dao = RuleCategoryDao()
    cat = dao.get_by_name(cat_name)
    if not cat:
        return ResponseBuilder.error_404()
    return Response(
        RuleSetParser.dumps(cat),
        status=201,
        mimetype="application/json"
    )


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search rule categories by name and phases.
    
    Returns:
        Response: JSON response containing the matching rule categories
    """
    name = request.args.get("name", type=str)
    phases_str = request.args.get("phases", type=str)
    phases = [int(phase) for phase in phases_str.split(",")] if phases_str else []
    
    dao = RuleCategoryDao()
    if name and phases:
        result = dao.get_by_name_and_phases(name, phases)
    else:
        result = dao.get_by_phases(phases)
    return ResponseBuilder.data_list(result, dao.schema)
