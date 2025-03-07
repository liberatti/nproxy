import json
import os
import sys
import traceback

import bcrypt

from api.common_utils import logger
from api.model.config_model import ConfigDao
from api.model.feed_model import FeedDao
from api.model.oauth_model import UserDao
from api.tools.security_feed_tool import RuleSetTool
from api.tools.security_feed_tool import SecurityFeedTool
from api.tools.ssl_tool import SSLTool
from config import APP_BASE

APP_CONFIG_DIR = os.path.join(APP_BASE, "admin/config")


def initialize_db():
    logger.info("Initialize DB")
    config_dao = ConfigDao()
    config_dao.drop_database()
    ca = SSLTool.gen_ca("Tooka-Internal", crt_org="Tooka")
    config_dao.persist(
        {
            "maxmind_key": "",
            "iblocklist_username": "liberatti.gustavo",
            "iblocklist_pin": "964647",
            "ca_certificate": SSLTool.crt_to_pem(ca["certificate"]),
            "ca_private": SSLTool.private_to_pem(ca["private_key"]),
            "acme_directory_url": "https://acme-v02.api.letsencrypt.org/directory",
        }
    )

    user_model = UserDao()
    logger.info("Create admin user")
    hashed = bcrypt.hashpw("admin".encode("utf8"), bcrypt.gensalt())
    user_model.persist(
        {
            "name": "Administrator",
            "email": "admin@local",
            "username": "admin",
            "password": hashed.decode("utf-8"),
            "role":"superuser"
        }
    )
    logger.info("Initialize DB completed")


def install():
    logger.info(f"Installation started")
    initialize_db()
    update()


def update():
    feed_dao = FeedDao()
    for arq_name in os.listdir(APP_CONFIG_DIR):
        feed = None
        try:
            if (
                    os.path.isfile(os.path.join(APP_CONFIG_DIR, arq_name))
                    and arq_name.startswith('feed-')
                    and arq_name.endswith('.json')
            ):
                with open(os.path.join(APP_CONFIG_DIR, arq_name), "r", encoding="utf-8") as arq:
                    feed = json.load(arq)
                    feed_o = feed_dao.get_by_slug(feed['slug'])
                    if feed_o:
                        feed_o.update(feed)
                        feed_dao.update_by_id(feed_o['_id'], feed)
                    else:
                        feed.update(
                            {
                                "scope": "system"
                            }
                        )
                        feed_dao.persist(feed)
        except Exception as e:
            logger.error(f"Failed to load {feed}: %s", e)
            logger.error(traceback.format_exc())

    RuleSetTool.update()
    SecurityFeedTool.update()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        'install': install,
        'update': update
    }

    fn = switch.get(sys.argv[1])
    fn()
