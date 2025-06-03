from flask import Blueprint, make_response, Response

from common_utils import ResponseBuilder
from model.acme_model import ChallengeDao

routes = Blueprint("acme", __name__)


@routes.route("/acme-challenge/<key>", methods=["GET"])
def get_config(key: str) -> Response:
    """
    Retrieve ACME challenge configuration for a given key.
    
    Args:
        key: The unique identifier for the ACME challenge
        
    Returns:
        Response: Plain text response with challenge content or 404 error
    """
    model = ChallengeDao()
    result = model.get_by_key(key)
    if result:
        response = make_response(result["content"], 200)
        response.mimetype = "text/plain"
        return response
    return ResponseBuilder.error_404()
