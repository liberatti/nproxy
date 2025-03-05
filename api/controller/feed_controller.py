from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, has_any_authority, get_pagination
from api.common_utils import socketio
from api.model.config_model import ChangeDao
from api.model.feed_model import FeedDao

routes = Blueprint("feed", __name__)


@routes.before_request
def before():
    if request.method in ["PUT", "POST", "DELETE"]:
        dao = ChangeDao()
        if not dao.get_by_name("feed"):
            dao.persist({"name": "feed"})
        socketio.emit('tracking_evt')


@routes.route("/<feed_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(feed_id):
    dao = FeedDao()
    feed = dao.get_by_id(feed_id)
    if feed:
        return ResponseBuilder.data(feed, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
    dao = FeedDao()
    try:
        feed_dict = dao.json_load(request.json)
        pk = dao.persist(feed_dict)
        feed = dao.get_by_id(pk)
        return ResponseBuilder.data(feed, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    dao = FeedDao()
    result = dao.get_all(pagination=get_pagination())
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<feed_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(feed_id):
    dao = FeedDao()
    try:
        feed_dict = dao.json_load(request.json)
        result = dao.update_by_id(feed_id, feed_dict)
        return ResponseBuilder.data(result, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<feed_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(feed_id):
    dao = FeedDao()
    result = dao.delete_by_id(feed_id)
    if result:
        return ResponseBuilder.data_removed(feed_id)
    else:
        return ResponseBuilder.error_404()
