import bcrypt
from flask import Blueprint, request
from marshmallow import ValidationError

from common_utils import ResponseBuilder, has_any_authority, jwt_decode, jwt_get, get_pagination
from model.oauth_model import UserDao

routes = Blueprint("user", __name__)


@routes.route("/<user_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(user_id):
    dao = UserDao()
    user = dao.get_by_id(user_id)
    if user:
        if "password" in user:
            user.pop("password")
        return ResponseBuilder.data(user, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save():
    dao = UserDao()
    try:
        vo = dao.json_load(request.json)
        if "password" in vo and len(vo["password"]) > 1:
            hashed = bcrypt.hashpw(vo["password"].encode("utf8"), bcrypt.gensalt())
            vo.update({"password":hashed.decode("utf-8")})
        dao.persist(vo)
        vo.pop("password")
        return ResponseBuilder.data(vo, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    dao = UserDao()
    result = dao.get_all(pagination=get_pagination())
    if result["metadata"]["total_elements"] > 0:
        for user in result['data']:
            if "password" in user:
                user.pop("password")
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<user_id>/account", methods=["PUT"])
@has_any_authority(authorities=["viewer", "superuser"])
def account_update(user_id):
    dao = UserDao()
    try:
        jwt_token = jwt_get()
        vo = dao.json_load(request.json)
        claims = jwt_decode(jwt_token)
        if claims["sub"] == user_id:
            if "password" in vo and len(vo["password"]) > 1:
                hashed = bcrypt.hashpw(vo["password"].encode("utf8"), bcrypt.gensalt())
                vo.update({"password": hashed.decode("utf-8")})
            result = dao.update_by_id(user_id, vo)
            return ResponseBuilder.data(result, dao.schema)
        else:
            return ResponseBuilder.error_403("Account update failed")
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<user_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(user_id):
    dao = UserDao()
    try:
        vo = dao.json_load(request.json)
        if "password" in vo and len(vo["password"]) > 1:
            hashed = bcrypt.hashpw(vo["password"].encode("utf8"), bcrypt.gensalt())
            vo.update({"password": hashed.decode("utf-8")})
        result = dao.update_by_id(user_id, vo)
        return ResponseBuilder.data(result, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<user_id>", methods=["DELETE"])
@has_any_authority(authorities=["superuser"])
def delete(user_id):
    dao = UserDao()
    r = dao.delete_by_id(user_id)
    if r:
        return ResponseBuilder.data_removed(user_id)
    else:
        return ResponseBuilder.error_404()
