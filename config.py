import os

import pytz

APP_VERSION="v1.0-alpha"
APP_BASE = "/opt/nproxy"

ENGINE_BASE = f"{APP_BASE}/nginx"
ENGINE_VERSION="1.27.1"


SECURITY_ENABLED = True

# Config database (MongoDB)
MONGO_URI=os.environ.get("MONGO_URI")

JWT_SECRET_KEY="dev"
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