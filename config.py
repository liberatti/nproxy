import os

import pytz

APP_VERSION = "v1.0.1-rc"
APP_BASE = "/opt/nproxy"

ENGINE_BASE = f"{APP_BASE}/nginx"
ENGINE_VERSION = "1.27.1"
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
TZ = pytz.timezone("UTC")

TELEMETRY_ENABLE = os.environ.get("TELEMETRY_ENABLE", True)
TELEMETRY_INTERVAL = os.environ.get("TELEMETRY_INTERVAL", 1)
TELEMETRY_URL = "https://nproxy.tooka.com.br"
MAINTENANCE_WINDOW = "01:00"

# Config database (MongoDB)
MONGO_HOST = os.environ.get("MONGO_HOST")
MONGO_PORT = os.environ.get("MONGO_PORT")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASS = os.environ.get("MONGO_PASS")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

# Security config
SECURITY_ENABLED = True
KEY_SIZE = 2048
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev")
JWT_EXPIRE = 3600
JWT_AUD = "nproxy"

# Cluster config
CLUSTER_ENDPOINT = os.environ.get("CLUSTER_ENDPOINT")
NODE_ROLE = os.environ.get("NODE_ROLE", "main")
NODE_KEY = os.environ.get("NODE_KEY", "DEV")
