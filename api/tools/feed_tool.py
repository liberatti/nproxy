import csv
import gzip
import io
import ipaddress
import os
import re
import socket
import tarfile
import traceback
from datetime import datetime
from zipfile import ZipFile

import geoip2.database
import requests
from marshmallow import ValidationError

from api.common_utils import logger, replace_tz
from api.model.config_model import ConfigDao
from api.model.dictionary_model import DictionaryDao
from api.model.feed_model import FeedDao
from api.model.geoip_model import GeoIpDao
from api.model.jail_model import JailDao
from api.model.seclang_model import RuleCategoryDao, RuleCategorySchema, RuleDao
from api.model.sensor_model import SensorDao
from api.model.service_model import ServiceDao
from api.model.transaction_model import TransactionDao
from api.tools.ruleset_tool import RuleSetParser
from config import APP_BASE, TZ


class JailTool:

    @classmethod
    def __is_jail_active(cls, services, jail):
        for s in services:
            for j in s["jails"]:
                if j["_id"] in jail["_id"]:
                    return True
        return False

    @classmethod
    def calc_process_jails(cls):
        dt = replace_tz(datetime.now())
        dao = JailDao()
        trn_dao = TransactionDao()
        srv_dao = ServiceDao()

        services = srv_dao.get_all()["data"]
        for j in dao.get_by_type("dynamic"):
            cs = {}

            bl = []
            for c in j["content"]:
                if (dt - replace_tz(c["banned_on"])).total_seconds() / 60 < j[
                    "bantime"
                ]:
                    bl.append(c)

            transactions = trn_dao.get_last_n_minutes(j["interval"])
            for t in transactions:
                if not cls.__is_jail_active(services, j):
                    pass
                source_ip = t["source"]["ip"]
                if source_ip not in cs:  # register source ip
                    cs[source_ip] = 0

                for rule in j["rules"]:
                    if "src.header" in rule["field"]:
                        for h in t["http"]["request"]["headers"]:
                            if re.search(rule["regex"], h["name"] + h["content"]):
                                cs[source_ip] += 1
                    if "src.request_line" in rule["field"]:
                        if re.search(
                            rule["regex"], t["http"]["request"]["request_line"]
                        ):
                            cs[source_ip] += 1
                    if "action" in rule["field"]:
                        if re.search(rule["regex"], t["action"]):
                            cs[source_ip] += 1
                    if "status_code" in rule["field"]:
                        if re.search(
                            rule["regex"], t["http"]["response"]["status_code"]
                        ):
                            cs[source_ip] += 1
            for ip, score in cs.items():
                if score >= j["occurrence"] and not any(
                    entry["ipaddr"] == ip for entry in bl
                ):
                    bl.append({"ipaddr": ip, "banned_on": dt})

            dao.update_by_id(j["_id"], {"content": bl})


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
            cls._download_crs(feed)
            total_rules = 0
            serializer = None
            if "crs" in feed["provider"]:
                serializer = RuleSetParser(
                    f"{APP_BASE}/data/{feed['slug']}-{feed['version']}/rules"
                )

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


class SecurityFeedTool:

    @classmethod
    def update(cls):
        dao = ConfigDao()
        conf = dao.get_active()
        feed_dao = FeedDao()
        dict_dao = DictionaryDao()

        for feed in feed_dao.get_by_type("network"):
            try:
                source_url = feed["source"]
                if feed["restricted"]:
                    if "iblocklist" in feed["provider"]:
                        if (
                            "iblocklist_username" in conf
                            and len(conf["iblocklist_username"]) > 0
                        ):
                            source_url = f"{source_url}&username={conf['iblocklist_username']}&pin={conf['iblocklist_pin']}"
                        else:
                            logger.info(f"Feed {feed['name']} skipped, no credentials")
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

                    content = []
                    for line in lines:
                        if line.strip() and "#" not in line:
                            if cls.is_ip_network(line):
                                content.append(line)
                    d = dict_dao.get_by_slug(feed["slug"])
                    if d:
                        dict_dao.update_by_id(d["_id"], {"content": content})
                    else:
                        dict_dao.persist(
                            {
                                "name": feed["name"],
                                "slug": feed["slug"],
                                "type": feed["type"],
                                "description": feed["description"],
                                "scope": "system",
                                "content": content,
                            }
                        )
                    feed_dao.update_by_id(feed["_id"], {"updated_on": datetime.now(TZ)})
                    logger.info(
                        f"Update Security IP feeds {feed['name']} with {len(content)} records"
                    )
            except Exception as e:
                logger.error(f"Failed to load {feed['slug']}: %s", e)
                logger.error(traceback.format_exc())
        cls.download_ip2asn()
        if "maxmind_key" in conf and len(conf["maxmind_key"]) > 0:
            cls.download_mmdb(conf["maxmind_key"], "GeoLite2-ASN")
            cls.download_mmdb(conf["maxmind_key"], "GeoLite2-City")

    @classmethod
    def is_ipv4(cls, ip):
        ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        return bool(re.match(ipv4_pattern, ip))

    @classmethod
    def expand_ip(cls, ip):
        if cls.is_ipv4(ip):
            parts = ip.split(".")
            parts_with_zero = [part.zfill(3) for part in parts]
            return ".".join(parts_with_zero)
        return str(ipaddress.ip_address(ip).exploded)

    @classmethod
    def compress_ip(cls, ip):
        if cls.is_ipv4(ip):
            return ".".join(str(int(o)) for o in ip.split("."))
        return str(ipaddress.ip_address(ip).compressed)

    @classmethod
    def calc_prefix_from_netmask(cls, ip_ini, mascara_str):
        net = ipaddress.ip_network(f"{ip_ini}/{mascara_str}", strict=False)
        return net.prefixlen

    @classmethod
    def calc_prefix_from_range(cls, ip_ini, ip_end):
        addr_ini = ipaddress.ip_address(cls.compress_ip(ip_ini))
        addr_end = ipaddress.ip_address(cls.compress_ip(ip_end))
        addr_total = int(addr_end) - int(addr_ini) + 1
        if addr_total <= 0:
            raise ValueError(f"{addr_ini} is greater than {addr_end}")
        num_bits = addr_total - 1
        if addr_ini.version == 4:
            prefix = 32 - num_bits.bit_length()
        elif addr_ini.version == 6:
            prefix = 128 - num_bits.bit_length()
        else:
            raise ValueError("Unsupported IP version")
        return prefix

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
                            "range_start": cls.expand_ip(row[0]),
                            "range_end": cls.expand_ip(row[1]),
                            "as_number": row[2],
                            "country_code": row[3],
                            "as_description": row[4],
                            "source": "ip2asn",
                            "version": 4 if cls.is_ipv4(row[0]) else 6,
                        }

                        if r["range_start"] and r["range_end"]:
                            prefix = cls.calc_prefix_from_range(
                                r["range_start"], r["range_end"]
                            )
                            r.update(
                                {
                                    "network": f"{cls.compress_ip(r['range_start'])}/{prefix}"
                                }
                            )
                            batch.append(r)
                    except Exception as e:
                        logger.error(f"Failed parse {r}: %s", e)
                        logger.error(traceback.format_exc())
                dao.persist_many(batch)
                logger.info(f"Download {feed} with {len(batch)} records")

    @classmethod
    def download_mmdb(cls, key, edition_id):
        url = f"https://download.maxmind.com/api.geoip_download?edition_id={edition_id}&license_key={key}&suffix=tar.gz"
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
    def info(cls, ip):
        ip = cls.expand_ip(ip)
        ip_info = {"addr": ip}
        model = GeoIpDao()
        ip_asn = model.find_by_ip(ip)
        if ip_asn:
            ip_info.update(
                {
                    "range_start": ip_asn["range_start"],
                    "range_end": ip_asn["range_end"],
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

    @classmethod
    def resolve(cls, ns):
        try:
            return socket.gethostbyname(ns)
        except socket.gaierror as e:
            logger.error(f"Name resolution failed for '{ns}': {e}")
            return None

    @classmethod
    def is_ip_addr(cls, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except Exception:
            return False

    @classmethod
    def is_ip_network(cls, net):
        try:
            ipaddress.ip_network(net, strict=False)
            return True
        except ipaddress.NetmaskValueError:
            return False
        except ValueError:
            return False

    @classmethod
    def aggregate(cls, addr_list):
        nets = [ipaddress.ip_network(ip) for ip in addr_list]
        nets = set(nets)
        nets = sorted(nets, key=lambda n: n.prefixlen)
        uq_nets = []
        while nets:
            n = nets.pop(0)
            if not any(n.subnet_of(un) for un in uq_nets):
                uq_nets.append(n)
        return [str(r) for r in uq_nets]

    @classmethod
    def expand_network(cls, masked_ip):
        network = ipaddress.IPv4Network(masked_ip, strict=False)
        return [str(ip) for ip in network.hosts()]
