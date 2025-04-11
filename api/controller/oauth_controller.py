import bcrypt
from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, jwt_decode, jwt_create_access_token, \
    jwt_create_refresh_token, jwt_get_refresh
from api.model.oauth_model import OIDCToken, UserDao
from config import ( JWT_EXPIRE)

routes = Blueprint("oauth", __name__)


@routes.route("/401", methods=["GET"])
def forbidden():
    return ResponseBuilder.error_401()


@routes.route("/token", methods=["GET"])
def refresh_token():
    r_token = jwt_get_refresh()
    payload = jwt_decode(r_token)
    user_dao = UserDao()
    user = user_dao.get_by_id(payload['sub'])
    if user:
        return {
            "access_token": jwt_create_access_token(user["_id"], authorities=[user["role"]], profile=user),
            "expires_in": JWT_EXPIRE,
            "token_type": 'bearer'
        }
    return ResponseBuilder.error_500(msg=f"Authorization failed for {payload['sub']}")


def _create_oidc_token(user):
    if "password" in user:
        user.pop("password")
    return {
        "access_token": jwt_create_access_token(user["_id"], authorities=[user['role']], profile=user),
        "refresh_token": jwt_create_refresh_token(user['_id']),
        "expires_in": JWT_EXPIRE,
        "token_type": 'bearer'
    }


@routes.route("/login", methods=["POST"])
def login():
    dao = UserDao()
    try:
        user_dict = dao.json_load(request.json)
        user = dao.get_by_email(user_dict["email"])
        if user and bcrypt.checkpw(
                user_dict["password"].encode("utf8"), user["password"].encode("utf8")
        ):
            return ResponseBuilder.data(_create_oidc_token(user), schema=OIDCToken())
        return ResponseBuilder.error_401("Sign in failed")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)
