import json
import os
import sys
import traceback

import bcrypt

from config import MONGO_DB
from common_utils import logger, gen_random_string,config_db
from model.config_model import ConfigDao
from model.feed_model import FeedDao
from model.oauth_model import UserDao
from tools.feed_tool import RuleSetTool, SecurityFeedTool
from tools.ssl_tool import SSLTool
from config import APP_BASE

APP_CONFIG_DIR = os.path.join(APP_BASE, "admin/config")

def update_schema():
    with open("config/mongo-schema.json", "r") as file:
        schema = json.load(file)
        database = getattr(config_db,schema['database'])
        for collection in schema['collections']:
            db_collection = database[collection['name']]
            if 'indexes' in collection:
                for index in collection['indexes']:
                    db_collection.create_index(index['name'])

def initialize_db():
    logger.info("Initialize DB")
    config_db.drop_database(MONGO_DB)
    update_schema()

    config_dao = ConfigDao()
    ca = SSLTool.gen_ca("Internal-CA", crt_org="NProxy")
    config_dao.persist(
        {
            "scn":None,
            "cluster_id": f"{gen_random_string(64)}",
            "maxmind_key": "",
            "iblocklist_username": "",
            "iblocklist_pin": "",
            "ca_certificate": SSLTool.crt_to_pem(ca["certificate"]),
            "ca_private": SSLTool.private_to_pem(ca["private_key"]),
            "acme_directory_url": "https://acme-v02.api.letsencrypt.org/directory",
            "telemetry": {
                "enabled": True,
                "url": "https://nproxy.app.br"
            }
        }
    )
    logger.debug("Create admin user")
    user_model = UserDao()
    user_model.persist(
        {
            "name": "Administrator",
            "email": "admin@local",
            "role": "superuser",
        }
    )

    reset_password(email="admin@local",psw="admin")
    logger.info("Initialize DB completed")

def install():
    logger.info(f"Installation started")
    initialize_db()
    update()

def update():
    update_schema()
    feed_dao = FeedDao()
    for arq_name in os.listdir(APP_CONFIG_DIR):
        feed = None
        try:
            if (
                os.path.isfile(os.path.join(APP_CONFIG_DIR, arq_name))
                and arq_name.startswith("feed-")
                and arq_name.endswith(".json")
            ):
                with open(
                    os.path.join(APP_CONFIG_DIR, arq_name), "r", encoding="utf-8"
                ) as arq:
                    feed = json.load(arq)
                    feed_o = feed_dao.get_by_slug(feed["slug"])
                    if feed_o:
                        feed_o.update(feed)
                        feed_dao.update_by_id(feed_o["_id"], feed)
                    else:
                        feed.update({"scope": "system"})
                        feed_dao.persist(feed)
        except Exception as e:
            logger.error(f"Failed to load {feed}: %s", e)
            logger.error(traceback.format_exc())

    RuleSetTool.update()
    SecurityFeedTool.update()
    logger.info(f"Update done")

def reset_password(email=None,psw=None):
    if not email:
        email = input("Enter email: ")
    if not psw:
        psw = input("Enter new password: ")
    user_model = UserDao()
    user = user_model.get_by_email(email)
    if not user:
        logger.error(f"User: {email} not found")
        sys.exit(1)
    hashed = bcrypt.hashpw(psw.encode("utf8"), bcrypt.gensalt())
    user_model.update_by_id(
        user["_id"], {"password": hashed.decode("utf-8"), "role": "superuser"}
    )
    logger.debug(f"User: {user['name']} reset is ok")

   

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "install": install,
        "update": update,
        "reset_password": reset_password
    }

    fn = switch.get(sys.argv[1])
    fn()
