import json
from datetime import datetime, timedelta

from elasticsearch import Elasticsearch

from common_utils import logger, deep_date_str
from model.transaction_model import TransactionDao
from tools.cluster_tool import ClusterTool
from config import TZ


class LogArchiverTool:
    @classmethod
    def auto_archive(cls):
        if ClusterTool.CONFIG:
            trn_dao = TransactionDao()
            now = datetime.now(TZ)
            if (
                "archive" in ClusterTool.CONFIG["config"]
                and ClusterTool.CONFIG["config"]["archive"]["enabled"]
            ):
                arch_config = ClusterTool.CONFIG["config"]["archive"]
                try:
                    dao = ElasticTool()
                    dao.create_schema()
                    arch_filter = [{"archived": False}]

                    dt_end = now - timedelta(minutes=arch_config["archive_after"])
                    trn_s = trn_dao.get_all(
                        dt_end=dt_end,
                        filters=arch_filter,
                        pagination={"per_page": 1000, "page": 1},
                    )

                    for trn in trn_s["data"]:
                        dao.send_transaction(trn)
                        trn_dao.update_by_id(trn["_id"], {"archived": True})
                    logger.info(
                        f"Archived {len(trn_s['data'])}/{trn_s['metadata']['total_elements']}"
                    )
                except Exception as e:
                    logger.error(e)

            


class ElasticTool:
    def __init__(self):
        try:
            arch_c = ClusterTool.CONFIG["config"]["archive"]
            if (
                "username" in arch_c
                and len(arch_c["username"] > 0)
                and "password" in arch_c
                and len(arch_c["password"] > 0)
            ):
                ha = (arch_c["username"], arch_c["password"])
                self.database = Elasticsearch([arch_c["url"]], http_auth=ha)
            else:
                self.database = Elasticsearch([arch_c["url"]])
        except ConnectionError as e:
            logger.info(f"Failed to connect %s", e)

    def create_schema(self):
        with open("config/elasticsearch-schema.json", "r") as file:
            idx_collection = json.load(file)
            for idx in idx_collection:
                self.database.indices.create(
                    index=idx.pop("index_name"), body=idx, ignore=400
                )

    def send_transaction(self, trn):
        _trn = deep_date_str(trn)
        _trn.pop("_id")
        _trn.pop("archived")

        req_headers = {
            item["name"]: item["content"]
            for item in _trn["http"]["request"].pop("headers")
        }
        _trn["http"]["request"].update({"headers": req_headers})

        res_headers = {
            item["name"]: item["content"]
            for item in _trn["http"]["response"].pop("headers")
        }
        _trn["http"]["request"].update({"headers": res_headers})

        self.database.index(index="nproxy_trn", document=_trn)
        # success, failed = bulk(es, documents)
