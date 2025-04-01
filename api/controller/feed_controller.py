from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import (
    ResponseBuilder,
    has_any_authority,
    get_pagination,
    socketio,
)
from api.model.config_model import ChangeDao
from api.model.feed_model import FeedDao
from api.model.rbl_model import RBLDao
from api.tools.network_tool import NetworkTool

routes = Blueprint("feed", __name__)


@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [
        200,
        201,
    ]:
        dao = ChangeDao()
        if not dao.get_by_name("feed"):
            dao.persist({"name": "feed"})
        socketio.emit("tracking_evt")
    return response


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
        if "network_static" in feed_dict["type"]:
            __rebuild_feed(feed_dict)
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
        if "network_static" in feed_dict["type"]:
            __rebuild_feed(feed_dict)
        dao.update_by_id(feed_id, feed_dict)
        return ResponseBuilder.data(feed_dict, dao.schema)
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


def __rebuild_feed(feed_dict):
    rbl_dao = RBLDao()
    rbl_dao.delete_by_provider("feed", feed_dict["_id"])
    for c in feed_dict["content"]:
        rbl = dict(NetworkTool.range_from_network(c))
        rbl.update(
            {
                "version": 4,
                "provider_type": "feed",
                "provider_id": feed_dict["_id"],
                "action": feed_dict["action"],
            }
        )
        rbl_dao.persist(rbl)
