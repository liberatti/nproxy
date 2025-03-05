from flask import Blueprint, request, Response

from api.common_utils import ResponseBuilder, has_any_authority
from api.model.seclang_model import RuleCategoryDao
from api.tools.ruleset_tool import RuleSetParser

routes = Blueprint("rulecat", __name__)


@routes.route("/<cat_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(cat_id):
    dao = RuleCategoryDao()
    cat = dao.get_by_id(cat_id)
    if cat:
        return Response(
            RuleSetParser.dumps(cat), status=201, mimetype="application/json"
        )
    else:
        return ResponseBuilder.error_404()


@routes.route("/by_name/<cat_name>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get_by_name(cat_name):
    dao = RuleCategoryDao()
    cat = dao.get_by_name(cat_name)
    if cat:
        return Response(
            RuleSetParser.dumps(cat), status=201, mimetype="application/json"
        )
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    name = request.args.get("name", type=str)
    phases_str = request.args.get("phases", type=str)
    phases = [int(phase) for phase in phases_str.split(",")]
    dao = RuleCategoryDao()
    if name and phases:
        result = dao.get_by_name_and_phases(name, phases)
    else:
        result = dao.get_by_phases(phases)
    return ResponseBuilder.data_list(result, dao.schema)
