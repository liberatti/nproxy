import os

import pytz

APP_VERSION="v1.0-alpha"
APP_BASE = "/opt/nproxy"

ENGINE_BASE = f"{APP_BASE}/nginx"
ENGINE_VERSION="1.27.1"


SECURITY_ENABLED = True

# Config database (MongoDB)
MONGO_HOST=os.environ.get("MONGO_HOST")
MONGO_PORT=os.environ.get("MONGO_PORT")
MONGO_DB=os.environ.get("MONGO_DB")
MONGO_USER=os.environ.get("MONGO_USER")
MONGO_PASS=os.environ.get("MONGO_PASS")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev")
JWT_EXPIRE=3600
JWT_AUD="nproxy"
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
ADMIN_ROLE = ["viewer", "superuser"]
KEY_SIZE=2048
CLUSTER_ENDPOINT = os.environ.get("CLUSTER_ENDPOINT", "http://172.17.0.1:5000")

NODE_ROLE = os.environ.get("NODE_ROLE", "main")
NODE_KEY = os.environ.get("NODE_KEY", "DEV")
TZ= pytz.timezone("UTC")
MAINTENANCE_WINDOW= "01:00"