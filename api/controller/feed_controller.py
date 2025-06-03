from bson import ObjectId
from typing import Dict, List, Optional, Union

from flask import Blueprint, request, Response
from marshmallow import ValidationError

from common_utils import (
    ResponseBuilder,
    has_any_authority,
    get_pagination,
    socketio,
)
from model.config_model import ChangeDao
from model.feed_model import FeedDao
from model.rbl_model import RBLDao
from tools.network_tool import NetworkTool

routes = Blueprint("feed", __name__)


@routes.after_request
def after(response: Response) -> Response:
    """
    Track changes after feed modifications.
    
    Args:
        response: The Flask response object
        
    Returns:
        Response: The modified response object
    """
    if request.method in ["PUT", "POST", "DELETE"] and response.status_code in [200, 201]:
        dao = ChangeDao()
        if not dao.get_by_name("feed"):
            dao.persist({"name": "feed"})
        socketio.emit("tracking_evt")
    return response


@routes.route("/<feed_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(feed_id: str) -> Response:
    """
    Retrieve a specific feed by ID.
    
    Args:
        feed_id: The unique identifier of the feed
        
    Returns:
        Response: JSON response containing the feed data or 404 error
    """
    dao = FeedDao()
    feed = dao.get_by_id(feed_id)
    return ResponseBuilder.data(feed, dao.schema) if feed else ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["superuser"])
def save() -> Response:
    """
    Create a new feed.
    If the feed type is 'network_static', it will also rebuild the feed.
    
    Returns:
        Response: JSON response containing the created feed or error message
    """
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
@has_any_authority(authorities=["viewer", "superuser"])
def search() -> Response:
    """
    Search and list all feeds.
    
    Returns:
        Response: JSON response containing paginated feed list or 404 error
    """
    dao = FeedDao()
    result = dao.get_all(pagination=get_pagination())
    return ResponseBuilder.data(result, dao.pageSchema) if result["metadata"]["total_elements"] > 0 else ResponseBuilder.error_404()


@routes.route("/<feed_id>", methods=["PUT"])
@has_any_authority(authorities=["superuser"])
def update(feed_id: str) -> Response:
    """
    Update an existing feed.
    If the feed type is 'network_static', it will also rebuild the feed.
    
    Args:
        feed_id: The unique identifier of the feed to update
        
    Returns:
        Response: JSON response containing the updated feed or error message
    """
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
@has_any_authority(authorities=["superuser"])
def delete(feed_id: str) -> Response:
    """
    Delete a feed.
    
    Args:
        feed_id: The unique identifier of the feed to delete
        
    Returns:
        Response: Success message or error response
    """
    dao = FeedDao()
    result = dao.delete_by_id(feed_id)
    return ResponseBuilder.data_removed(feed_id) if result else ResponseBuilder.error_404()


def __rebuild_feed(feed_dict: Dict) -> None:
    """
    Rebuild the feed by processing its content and updating RBL entries.
    
    Args:
        feed_dict: The feed dictionary containing content to process
    """
    rbl_dao = RBLDao()
    rbl_dao.delete_by_provider("feed", feed_dict["_id"])
    
    for content in feed_dict["content"]:
        rbl = dict(NetworkTool.range_from_network(content))
        rbl.update({
            "provider_type": "feed",
            "provider_id": ObjectId(feed_dict["_id"]),
            "action": feed_dict["action"],
        })
        rbl_dao.persist(rbl)
