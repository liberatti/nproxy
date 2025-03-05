from flask import Blueprint, make_response

from api.common_utils import ResponseBuilder
from api.model.acme_model import ChallengeDao

routes = Blueprint("acme", __name__)


@routes.route("/acme-challenge/<key>", methods=["GET"])
def get_config(key):
    model = ChallengeDao()
    result = model.get_by_key(key)
    if result:
        response = make_response(result["content"], 200)
        response.mimetype = "text/plain"
        return response
    else:
        return ResponseBuilder.error_404()
