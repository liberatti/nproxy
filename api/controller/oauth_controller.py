import traceback
import bcrypt
from typing import Dict, List, Optional, Union

from flask import Blueprint, request, Response
from marshmallow import ValidationError

from common_utils import (
    ResponseBuilder,
    jwt_decode,
    jwt_create_access_token,
    jwt_create_refresh_token,
    jwt_get_refresh
)
from model.oauth_model import OIDCToken, UserDao
from config import JWT_EXPIRE

routes = Blueprint("oauth", __name__)


@routes.route("/401", methods=["GET"])
def forbidden() -> Response:
    """
    Return a 401 Unauthorized response.
    
    Returns:
        Response: 401 Unauthorized error response
    """
    return ResponseBuilder.error_401()


@routes.route("/token", methods=["GET"])
def refresh_token() -> Response:
    """
    Refresh an access token using a refresh token.
    
    Returns:
        Response: New access token or error response
    """
    r_token = jwt_get_refresh()
    try:
        payload = jwt_decode(r_token)
        user_dao = UserDao()
        user = user_dao.get_by_id(payload['sub'])
        if not user:
            return ResponseBuilder.error_500(msg=f"Authorization failed for {payload['sub']}")
            
        return {
            "access_token": jwt_create_access_token(user["_id"], authorities=[user["role"]], profile=user),
            "expires_in": JWT_EXPIRE,
            "token_type": 'bearer'
        }
    except Exception as e:
        return ResponseBuilder.error_500(msg=f"Authorization failed for {r_token}",details=traceback.format_exc())


def _create_oidc_token(user: Dict) -> Dict:
    """
    Create OIDC tokens for a user.
    
    Args:
        user: The user dictionary containing user information
        
    Returns:
        Dict: Dictionary containing access token, refresh token, and token information
    """
    if "password" in user:
        user.pop("password")
    return {
        "access_token": jwt_create_access_token(user["_id"], authorities=[user['role']], profile=user),
        "refresh_token": jwt_create_refresh_token(user['_id']),
        "expires_in": JWT_EXPIRE,
        "token_type": 'bearer'
    }


@routes.route("/login", methods=["POST"])
def login() -> Response:
    """
    Authenticate a user and return OIDC tokens.
    
    Returns:
        Response: OIDC tokens or error response
    """
    dao = UserDao()
    try:
        user_dict = dao.json_load(request.json)
        user = dao.get_by_email(user_dict["email"])
        
        if user and bcrypt.checkpw(
            user_dict["password"].encode("utf8"),
            user["password"].encode("utf8")
        ):
            return ResponseBuilder.data(_create_oidc_token(user), schema=OIDCToken())
            
        return ResponseBuilder.error_401("Sign in failed")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)
