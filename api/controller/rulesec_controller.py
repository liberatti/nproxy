from flask import Blueprint

from api.common_utils import ResponseBuilder, has_any_authority
from api.model.seclang_model import RuleDao

routes = Blueprint("rulesec", __name__)


@routes.route("/by_code/<rule_code>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(rule_code):
    dao = RuleDao()
    vo = dao.get_by_code(rule_code)
    if vo:
        return ResponseBuilder.data(vo)
    else:
        return ResponseBuilder.error_404()
