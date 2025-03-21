from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, has_any_authority, get_pagination
from api.common_utils import socketio
from api.model.config_model import ChangeDao
from api.model.dictionary_model import DictionaryDao

routes = Blueprint("dictionary", __name__)

@routes.after_request
def after(response):
    if request.method in ["PUT", "POST", "DELETE"] and  response.status_code in [200,201]:
        dao = ChangeDao()
        if not dao.get_by_name("dictionary"):
            dao.persist({"name": "dictionary"})
        socketio.emit('tracking_evt')
    return response

@routes.route("/<dictionary_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(dictionary_id):
    dao = DictionaryDao()
    dictionary = dao.get_by_id(dictionary_id)
    if dictionary:
        return ResponseBuilder.data(dictionary, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
    dao = DictionaryDao()
    try:
        dictionary_dict = dao.json_load(request.json)
        pk = dao.persist(dictionary_dict)
        dictionary = dao.get_by_id(pk)
        return ResponseBuilder.data(dictionary, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    dao = DictionaryDao()
    _pagination = get_pagination()
    _filters = []
    if request.args.get('user_only', 'false').lower() == 'true':
        _filters.append({
            'scope': 'user'
        })

    if 'regex' in request.args and len(request.args.get('regex')) > 0:
        _r = request.args.get('regex')
        _filters.append({
            '$or': [
                {'name': {'$regex': f"^.*{_r}.*$", '$options': "i"}},
                {'content': {'$elemMatch': {'$regex': _r}}}
            ]
        })

    result = dao.get_all(
        pagination=_pagination,
        filters=_filters
    )
    for r in result["data"]:
        if 'content' in r:
            r.pop("content")
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<dictionary_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(dictionary_id):
    dao = DictionaryDao()
    try:
        dictionary_dict = dao.json_load(request.json)
        result = dao.update_by_id(dictionary_id, dictionary_dict)
        return ResponseBuilder.data(result, dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)


@routes.route("/<dictionary_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(dictionary_id):
    dao = DictionaryDao()
    result = dao.delete_by_id(dictionary_id)
    if result:
        return ResponseBuilder.data_removed(dictionary_id)
    else:
        return ResponseBuilder.error_404()
