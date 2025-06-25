import csv
import gzip
import io
import os
import re
import tarfile
import traceback
from datetime import datetime, timedelta
from zipfile import ZipFile

import geoip2.database
import requests
from bson import ObjectId
from marshmallow import ValidationError

from common_utils import logger, replace_tz
from model.config_model import ConfigDao
from model.feed_model import FeedDao
from model.geoip_model import GeoIpDao
from model.jail_model import JailDao
from model.rbl_model import RBLDao
from model.seclang_model import RuleCategoryDao, RuleCategorySchema, RuleDao
from model.sensor_model import SensorDao
from model.transaction_model import TransactionDao
from tools.network_tool import NetworkTool
from tools.ruleset_tool import RuleSetParser
from config import APP_BASE, TZ


class JailTool:

    @classmethod
    def calc_process_jails(cls):
        now_dt = replace_tz(datetime.now())
        dao = JailDao()
        trn_dao = TransactionDao()
        sensor_dao = SensorDao()
        rbl_dao = RBLDao()
        for j in dao.get_all()["data"]:
            sensor_ids = sensor_dao.get_ids_by_jail(j["_id"])
            if sensor_ids and len(sensor_ids) > 0:
                transactions = trn_dao.get_last_n_minutes(
                    j["interval"], sensor_ids=sensor_ids
                )
                cs = {}
                for t in transactions:
                    source_ip = t["source"]["ip"]
                    if source_ip not in cs:  # register source ip
                        cs[source_ip] = 0
                    for rule in j["rules"]:
                        if "src.header" in rule["field"]:
                            pattern = re.compile(rule["regex"], re.IGNORECASE)
                            for h in t["http"]["request"]["headers"]:
                                if pattern.search(h["content"]):
                                    cs[source_ip] += 1
                        if "src.request_line" in rule["field"]:
                            if re.search(rule["regex"], t["http"]["request_line"]):
                                cs[source_ip] += 1
                        if "status_code" in rule["field"]:
                            if re.search(
                                rule["regex"], t["http"]["response"]["status_code"]
                            ):
                                cs[source_ip] += 1
                for ip, score in cs.items():
                    if score >= j["occurrence"]:
                        b = NetworkTool.range_from_network(ip)
                        b.update(
                            {
                                "provider_type": "jail",
                                "provider_id": ObjectId(j["_id"]),
                                "action": "deny",
                            }
                        )
                        ck_upd = rbl_dao.update_by_query(b, {"banned_on": now_dt})
                        if not ck_upd:
                            b.update({"banned_on": now_dt})
                            rbl_dao.persist(b)
            rbl_dao.delete_expired(
                "jail", j["_id"], now_dt - timedelta(minutes=j["bantime"])
            )


class RuleSetTool:
    @classmethod
    def _download_crs(cls, feed_config):
        if not os.path.exists(
            f"{APP_BASE}/data/{feed_config['slug']}-{feed_config['version']}"
        ):
            logger.info(
                f"Download CRS {feed_config['version']} from {feed_config['source']}"
            )
            response = requests.get(feed_config["source"])
            if response.status_code == 200:
                zip_content = io.BytesIO(response.content)
                os.makedirs(f"{APP_BASE}/data", exist_ok=True)
                with ZipFile(zip_content, "r") as zip_ref:
                    zip_ref.extractall(f"{APP_BASE}/data")
            else:
                logger.error(f"Failed to download {feed_config['slug']} {response}")

    @classmethod
    def update_default_sensor(cls):
        dao = SensorDao()
        dao_cat = RuleCategoryDao()
        sensor = dao.get_by_name("Default")
        if sensor:
            sensor_id = sensor["_id"]
        else:
            exclusions = []
            for c in dao_cat.get_by_phases([3, 5]):
                if "exclusions" in c:
                    exclusions.extend(c["exclusions"])

            sensor_id = dao.persist(
                {
                    "name": "Default",
                    "description": "Default Security Sensor",
                    "permit": [],
                    "block": [],
                    "exclusions": exclusions,
                    "categories": [],
                }
            )

        categories = []
        for c in dao_cat.get_by_phases([3, 5]):
            categories.append(c["name"])
        dao.update_by_id(sensor_id, {"categories": categories})

    @classmethod
    def update(cls):
        feed_dao = FeedDao()
        for feed in feed_dao.get_by_type("ruleset"):
            logger.info(f"Updating ruleset {feed['slug']}")
            total_rules = 0
            serializer = None
            try:
                if feed["provider"] == "crs":
                    cls._download_crs(feed)
                    serializer = RuleSetParser(f"{APP_BASE}/data/{feed['slug']}-{feed['version']}/rules")
                    dao_rule = RuleDao()
                    dao_rule.delete_all()

                    dao = RuleCategoryDao()
                    dao.delete_all()

                    try:
                        categories = []
                        for cat in feed["mapping"]:
                            c = RuleCategorySchema().load(cat)
                            if "file" in cat:
                                c.update(
                                    {"rules": serializer.read_file_as_seclang(cat["file"])}
                                )
                            else:
                                rules = []
                                for r in cat["rules"]:
                                    rules.append(RuleSetParser.load(r))
                                c.update({"rules": rules})
                            categories.append(c)
                            total_rules += len(c["rules"])
                        for cat in categories:
                            dao.persist(cat)
                        logger.info(f"Indexed {total_rules} rules from {feed['slug']}")
                        cls.update_default_sensor()
                    except ValidationError as e:
                        logger.error(f"Failed to load {feed['slug']}: %s", e.messages)
                        logger.error(traceback.format_exc())
            except Exception as e1:
                    logger.error(f"Failed to update {feed['slug']}: %s", e.messages)


class SecurityFeedTool:

    @classmethod
    def update(cls):
        dao = ConfigDao()
        conf = dao.get_active()

        cls.download_ip2asn()
        if "maxmind_key" in conf and len(conf["maxmind_key"]) > 0:
            try:
                cls.download_mmdb(conf["maxmind_key"], "GeoLite2-ASN")
                cls.download_mmdb(conf["maxmind_key"], "GeoLite2-City")
            except Exception as e:
                logger.error(f"Failed to download GeoLite2: %s", e)
                
        feed_dao = FeedDao()
        for feed in feed_dao.get_by_type("network"):
            if "source" in feed and len(feed["source"]) > 1:
                try:
                    source_url = feed["source"]
                    rbl_dao = RBLDao()
                    if feed["restricted"]:
                        if "iblocklist" in feed["provider"]:
                            if (
                                "iblocklist_username" in conf
                                and len(conf["iblocklist_username"]) > 0
                            ):
                                source_url = f"{source_url}&username={conf['iblocklist_username']}&pin={conf['iblocklist_pin']}"
                            else:
                                logger.info(
                                    f"Feed {feed['name']} skipped, no credentials"
                                )
                                continue

                    resp = requests.get(source_url)
                    if resp and resp.status_code == 200:
                        lines = []
                        if "cdir_text" in feed["format"]:
                            lines = resp.text.splitlines()
                        if "cdir_gz" in feed["format"]:
                            with gzip.GzipFile(fileobj=io.BytesIO(resp.content)) as gz:
                                for l in gz:
                                    lines.append(l.decode("utf-8").strip())
                        rbl_dao.delete_by_provider("feed", feed["_id"])
                        fc = 0
                        for line in lines:
                            if line.strip() and "#" not in line:
                                if NetworkTool.is_network(line):
                                    rbl = dict(NetworkTool.range_from_network(line))
                                    ip_v = (
                                        4
                                        if NetworkTool.is_ipv4(line.split("/")[0])
                                        else 6
                                    )
                                    rbl.update(
                                        {
                                            "version": ip_v,
                                            "provider_type": "feed",
                                            "provider_id": ObjectId(feed["_id"]),
                                            "action": feed["action"],
                                        }
                                    )
                                    rbl_dao.persist(rbl)
                                    fc += 1

                        feed_dao.update_by_id(
                            feed["_id"], {"updated_on": datetime.now(TZ)}
                        )
                        logger.info(
                            f"Update Security IP feeds {feed['name']} with {fc} records"
                        )
                except Exception as e:
                    logger.error(f"Failed to load {feed['slug']}: %s", e)
                    logger.error(traceback.format_exc())

    @classmethod
    def download_ip2asn(cls, feed="ip2asn-combined"):
        response = requests.get(f"https://iptoasn.com/data/{feed}.tsv.gz")
        if response.status_code == 200:
            dao = GeoIpDao()
            dao.delete_all()
            zip_content = io.BytesIO(response.content)
            with gzip.open(zip_content, "rt", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter="\t")
                batch = []
                for row in reader:
                    try:
                        r = {
                            "as_number": row[2],
                            "country_code": row[3],
                            "as_description": row[4],
                            "source": "ip2asn",
                            "version": 4 if NetworkTool.is_ipv4(row[0]) else 6,
                            "network": f"{row[0]}/{NetworkTool.calc_prefix_from_range(row[0], row[1])}",
                        }
                        r.update(NetworkTool.range_from_network(r["network"]))
                        batch.append(r)
                    except Exception as e:
                        logger.error(f"Failed parse {r}: %s", e)
                        logger.error(traceback.format_exc())
                dao.persist_many(batch)
                logger.info(f"Download {feed} with {len(batch)} records")

    @classmethod
    def download_mmdb(cls, key, edition_id):
        url = f"https://download.maxmind.com/geoip_download?edition_id={edition_id}&license_key={key}&suffix=tar.gz"
        logger.info(f"{url}")
        response = requests.get(url)
        if response.status_code == 200:
            zip_content = io.BytesIO(response.content)
            with tarfile.open(fileobj=zip_content, mode="r:gz") as tar:
                for m in tar.getmembers():
                    if ".mmdb" in m.name:
                        tar.extract(m, path=f"{APP_BASE}/data")
                        os.rename(
                            f"{APP_BASE}/data/{m.name}",
                            f"{APP_BASE}/data/{edition_id}.mmdb",
                        )
                        os.rmdir(f"{APP_BASE}/data/{m.name.split('/')[0]}")
        else:
            logger.error(f"Failed to download {edition_id} {response}")
        logger.info(f"[update] Download {edition_id}")

    @classmethod
    def geo_info(cls, ip):
        ip_info = {}
        model = GeoIpDao()
        ip_asn = model.find_by_ip(ip)
        if ip_asn:
            ip_info.update(
                {
                    "net_start": ip_asn["net_start"],
                    "net_end": ip_asn["net_end"],
                    "ans_number": ip_asn["as_number"],
                    "organization": ip_asn["as_description"],
                    "country": ip_asn["country_code"],
                }
            )
        for db in ["ASN", "City"]:
            if os.path.exists(f"{APP_BASE}/data/GeoLite2-{db}.mmdb"):
                with geoip2.database.Reader(
                    f"{APP_BASE}/data/GeoLite2-{db}.mmdb"
                ) as reader:
                    try:
                        if "ASN" in db:
                            response_asn = reader.asn(ip)
                            ip_info.update(
                                {
                                    "ans_number": response_asn.autonomous_system_number,
                                    "organization": response_asn.autonomous_system_organization,
                                }
                            )
                        if "City" in db:
                            response_city = reader.city(ip)
                            ip_info.update(
                                {
                                    "country": response_city.country.iso_code,
                                    "latitude": response_city.location.latitude,
                                    "longitude": response_city.location.longitude,
                                }
                            )
                    except Exception:
                        pass
        return ip_info
