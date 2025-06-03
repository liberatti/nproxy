import base64
import hashlib
import inspect
import json
import logging
import os
import random
import shutil
import socket
import string
import threading
import traceback
import zipfile
from copy import deepcopy
from datetime import datetime, timedelta
from functools import wraps

import jwt
import pymongo
from bson import ObjectId
from flask import jsonify, request
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO
from jwt import ExpiredSignatureError
from marshmallow import Schema, fields

from config import (
    JWT_AUD,
    JWT_EXPIRE,
    NODE_KEY,
    NODE_ROLE,
    SECURITY_ENABLED,
    MONGO_URI,
    JWT_SECRET_KEY,
    TZ,
    APP_VERSION,
)

ma = Marshmallow()
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
API_HEADERS = {"User-Agent": f"Nproxy/{APP_VERSION}", "x-cluster-key": NODE_KEY}


def clear_directory(directory_path):
    if os.path.exists(directory_path):
        try:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            logger.error(e)


def unpack_zip(content, target_dir="/var/www"):
    os.mkdir(target_dir)
    zip_file_path = os.path.join(target_dir, "unpack.zip")
    with open(zip_file_path, "wb") as zip_file:
        zip_file.write(content)
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    os.remove(zip_file_path)


def get_server_id():
    server_ = os.getenv("SERVERID")
    if server_ is None:
        server_ = socket.getfqdn()
    return server_


def print_request(req):
    logger.info(f"Request: [{req.method}] {req.url} ({req.content_type})")
    for key, value in req.form.items():
        logger.info(f"FormData: {key}={value}")
    logger.info(f"Files upload: {req.files.keys()}")
    for filename, file in req.files.items():
        logger.info(f"FileData: {filename} ({file.content_type}) {file.read(100)}..")
    for header, value in req.headers.items():
        logger.info(f"Header: {header}={value}")
    for key, value in req.args.items():
        logger.info(f"QueryData: {key}={value}")


def deep_date_str(obj):
    _obj = deepcopy(obj)
    for key, value in _obj.items():
        if isinstance(value, datetime):
            _obj[key] = value.isoformat()
        elif isinstance(value, dict):
            deep_date_str(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    deep_date_str(item)
    return _obj


def deep_merge(a: dict, b: dict) -> dict:
    result = deepcopy(a)
    for bk, bv in b.items():
        av = result.get(bk)
        if isinstance(av, dict) and isinstance(bv, dict):
            result[bk] = deep_merge(av, bv)
        else:
            result[bk] = deepcopy(bv)
    return result


def hash_dict(d):
    json_str = json.dumps(d, sort_keys=True, default=json_serial)
    return hashlib.md5(json_str.encode()).hexdigest()


def get_pagination():
    _pagination = None
    if "size" in request.args and "page" in request.args:
        _pagination = {
            "per_page": int(request.args.get("size")),
            "page": int(request.args.get("page")),
        }
    return _pagination


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"non-serializable type: {type(obj)}")


def jwt_get():
    token = request.headers.get("Authorization")
    return token.split(" ")[1] if " " in token else token


def jwt_get_refresh():
    return request.headers.get("Refresh-Token")


def jwt_decode(token):
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"], audience=JWT_AUD)


def jwt_create_access_token(sub, profile=None, authorities=None):
    now = datetime.now(TZ)
    if profile:
        profile.pop("created_at", None)
        profile.pop("updated_at", None)
        profile.pop("password", None)
    payload = {
        "exp": int((now + timedelta(seconds=JWT_EXPIRE)).timestamp()),
        "iat": int(now.timestamp()),
        "sub": sub,
        "profile": profile,
        "authorities": authorities,
        "aud": JWT_AUD,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def jwt_create_refresh_token(sub):
    now = datetime.now(TZ) + timedelta(hours=24)
    payload = {"exp": int(now.timestamp()), "sub": sub, "aud": JWT_AUD}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def gen_random_string(length=16):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def has_any_authority(authorities=None,_internal=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not SECURITY_ENABLED:
                return fn(*args, **kwargs)
            if "main" in NODE_ROLE and _internal:
                if NODE_KEY == request.headers.get("x-cluster-key"):
                    return fn(*args, **kwargs)
            try:
                token = jwt_get()
                payload = jwt_decode(token)
                if any(a in payload.get("authorities", []) for a in authorities):
                    return fn(*args, **kwargs)
            except ExpiredSignatureError:
                return ResponseBuilder.error_401(
                    msg="Expired authorization", details=traceback.format_exc()
                )
            except Exception as e2:
                return ResponseBuilder.error_401(
                    msg=str(e2), details=traceback.format_exc()
                )
            return ResponseBuilder.error_403(message="Invalid authorization")

        return decorator

    return wrapper

def replace_tz(not_valid_before):
    if not_valid_before.tzinfo is None:
        crt_not_valid_before = not_valid_before.replace(tzinfo=TZ)
    else:
        crt_not_valid_before = not_valid_before
    return crt_not_valid_before.astimezone(TZ)


class CustomLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        frame = inspect.currentframe().f_back
        caller_method = frame.f_code.co_name
        filename = os.path.basename(frame.f_globals.get("__file__", ""))
        lineno = frame.f_lineno
        super().info(f"[{filename}][{caller_method}][{lineno}] {msg}", *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        frame = inspect.currentframe().f_back
        caller_method = frame.f_code.co_name
        filename = os.path.basename(frame.f_globals.get("__file__", ""))
        lineno = frame.f_lineno
        super().error(f"[{filename}][{caller_method}][{lineno}] {msg}", *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        frame = inspect.currentframe().f_back
        caller_method = frame.f_code.co_name
        filename = os.path.basename(frame.f_globals.get("__file__", ""))
        lineno = frame.f_lineno
        super().warn(f"[{filename}][{caller_method}][{lineno}] {msg}", *args, **kwargs)


logger = CustomLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - :name - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

config_db = pymongo.MongoClient(
    MONGO_URI, maxPoolSize=None, socketTimeoutMS=30000, connectTimeoutMS=30000
)


class ResponseBuilder:

    @classmethod
    def error_404(cls):
        return (
            jsonify(
                {
                    "message": "No results found. Check url again",
                    "code": 404,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            200,
        )

    @classmethod
    def error(cls, msg="Bad Request", details="", code=400):
        return (
            jsonify(
                {
                    "message": msg,
                    "code": code,
                    "details": details,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            code,
        )

    @classmethod
    def error_401(cls, msg="Not authenticated", details=""):
        return (
            jsonify(
                {
                    "message": msg,
                    "code": 401,
                    "details": details,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            401,
        )

    @classmethod
    def error_403(cls, message="Not authorized"):
        return (
            jsonify(
                {
                    "message": message,
                    "code": 403,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            403,
        )

    @classmethod
    def error_500(cls, msg, code=500, details=""):
        return (
            jsonify(
                {
                    "message": msg,
                    "details": details,
                    "code": code,
                    "url": request.url,
                    "method": request.method,
                }
            ),
            500,
        )

    @classmethod
    def data_removed(cls, desc):
        return (
            jsonify({"message": f"Record {desc} removed", "code": 200}),
            200,
        )

    @classmethod
    def ok(cls, desc):
        return (
            jsonify({"message": desc, "code": 200}),
            200,
        )

    @classmethod
    def error_parse(cls, err):
        return (
            jsonify(
                {
                    "message": "Validation Error",
                    "details": err.messages,
                    "code": 400,
                    "url": request.url,
                    "method": request.method,
                    # "valid_data": err.valid_data,
                }
            ),
            400,
        )

    @classmethod
    def data_list(cls, o, schema=None):
        if schema:
            return [schema.dump(i) for i in o]
        else:
            return jsonify(o), 200

    @classmethod
    def data(cls, o, schema=None):
        if schema:
            return jsonify(schema.dump(o)), 200
        else:
            return jsonify(o), 200


class LogCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.audit_log = []
        self.access_log = []
        self.error_log = []


class PageMetaSchema(Schema):
    total_elements = fields.Integer()
    page = fields.Integer()
    per_page = fields.Integer()
