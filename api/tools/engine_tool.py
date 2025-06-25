import copy
import json
import os
import pickle
import time
import traceback
from collections import OrderedDict

import requests
from marshmallow import ValidationError

from common_utils import (
    gen_random_string,
    hash_dict,
    logger,
    get_server_id,
    unpack_zip,
    clear_directory,
    API_HEADERS,
)
from model.certificate_model import CertificateDao
from model.config_model import ConfigDao
from model.feed_model import FeedDao
from model.jail_model import JailDao
from model.seclang_model import RuleCategoryDao, SecAction, SecRule
from model.sensor_model import SensorDao
from model.service_model import ServiceDao
from model.upstream_model import UpstreamDao
from tools.ruleset_tool import RuleSetParser
from config import APP_BASE, CLUSTER_ENDPOINT, ENGINE_BASE, NODE_ROLE, NODE_KEY
from tools.network_tool import NetworkTool


# noinspection PyMethodMayBeStatic
class EngineManager:
    __LOG_FORMAT = '{"time":"$time_local","service_id":"$service_id","route_name":"$route_name","upstream_id":"$upstream_id","target_addr":"$upstream_addr","sensor_id":"$sensor_id","uniqueid":"$request_id","host":"$http_host","remote_addr":"$remote_addr","remote_port":$remote_port,"server_port":$server_port,"request_line":"$request","method":"$real_method","status":$status,"bytes_in":$request_length,"bytes_out":$body_bytes_sent,"duration":$request_time,"uht":"$upstream_header_time","urt":"$upstream_response_time","referer":"$http_referer","user_agent":"$http_user_agent","limit_req_status":"$limit_req_status","geoip_status":"$geoip_status","rbl_status":"$rbl_status"}'
    CONFIG = None

    nginx = f"{ENGINE_BASE}/sbin/nginx"
    max_retries = 10

    def __init__(self, startup=False):
        self._init_dir()
        if "main" in NODE_ROLE:
            if startup:  # READ START_CONFIG
                with open(f"{APP_BASE}/run/activated.config", "rb") as f:
                    self.CONFIG = pickle.load(f)
            else:
                upstream_page = UpstreamDao().get_all()
                certificate_page = CertificateDao().get_all()
                feed_page = FeedDao().get_all()
                service_page = ServiceDao().get_all()
                sensor_page = SensorDao().get_all()
                rule_page = RuleCategoryDao().get_all()
                jail_page = JailDao().get_all()
                conf = ConfigDao().get_active()
                self.CONFIG = {
                    "config": conf,
                    "certificates": certificate_page["data"],
                    "upstreams": upstream_page["data"],
                    "feeds": feed_page["data"],
                    "services": service_page["data"],
                    "sensors": sensor_page["data"],
                    "categories": rule_page["data"],
                    "jails": jail_page["data"],
                }
                self.CONFIG.update({"scn": hash_dict(self.CONFIG)})
        else:
            attempt = 0
            while attempt < self.max_retries:
                try:
                    response = requests.get(
                        f"{CLUSTER_ENDPOINT}/api/replica/scn", headers=API_HEADERS
                    )
                    if response.status_code in [200, 201]:
                        check = response.json()
                        if self.CONFIG and check["scn"] in self.CONFIG["scn"]:
                            logger.info(
                                f"Keep {self.CONFIG['scn']} for {NODE_ROLE} {CLUSTER_ENDPOINT}"
                            )
                        else:
                            response = requests.get(
                                f"{CLUSTER_ENDPOINT}/api/replica/config",
                                headers=API_HEADERS,
                            )
                            self.CONFIG = response.json()
                            break
                    else:
                        logger.error(
                            f"[{response.status_code}] Failed to get config, check {CLUSTER_ENDPOINT}"
                        )
                except requests.RequestException as e:
                    logger.error("Request failed: %s", e)
                    stack_trace = traceback.format_exc()
                    logger.error(stack_trace)
                attempt += 1
                time.sleep(10)

    def _init_dir(self):
        os.makedirs(f"{APP_BASE}/run", exist_ok=True)
        os.makedirs(f"{APP_BASE}/temp/", exist_ok=True)
        os.makedirs(f"{APP_BASE}/logs", exist_ok=True)
        for f in [
            "client_body",
            "fastcgi_temp",
            "proxy_temp",
            "scgi_temp",
            "uwsgi_temp",
        ]:
            os.makedirs(f"{APP_BASE}/temp/{f}", exist_ok=True)

    def _get_config_rules(self):
        app_config_dir = os.path.join(APP_BASE, "admin/config")
        for arq_name in os.listdir(app_config_dir):
            try:
                if (
                    os.path.isfile(os.path.join(app_config_dir, arq_name))
                    and arq_name.startswith("feed-")
                    and arq_name.endswith(".json")
                ):
                    with open(
                        os.path.join(app_config_dir, arq_name), "r", encoding="utf-8"
                    ) as arq:
                        feed = json.load(arq)
                        if "ruleset" in feed["type"]:
                            rules = []
                            for r in feed["config"]:
                                rules.append(RuleSetParser.load(r))
                            return rules
            except ValidationError as e:
                logger.error(f"Failed to load {arq_name}: %s", e.messages)
                logger.error(traceback.format_exc())

    # noinspection PyListCreation
    def _build_config_policy(self):
        pcre = 10000
        sb = []
        sb.append(f"SecPcreMatchLimit {pcre}")
        sb.append(f"SecPcreMatchLimit {pcre}")
        sb.append(f"SecPcreMatchLimitRecursion {pcre}")
        sb.append(f"SecDataDir /tmp/modsec")
        sb.append(f"SecRequestBodyLimitAction Reject")
        sb.append(f"SecRequestBodyAccess On")

        sb.append(f"SecResponseBodyAccess On")
        sb.append(f"SecResponseBodyLimitAction ProcessPartial")
        sb.append(
            f"SecResponseBodyMimeType text/plain text/html text/xml application/json"
        )
        sb.append(f"SecArgumentSeparator &")
        sb.append(f"SecCookieFormat 0")
        sb.append(f"SecCollectionTimeout 600")
        sb.append(f'SecDefaultAction "phase:1,log,auditlog,pass"')
        sb.append(f'SecDefaultAction "phase:2,log,auditlog,pass"')

        for r in self._get_config_rules():
            sb.append(RuleSetParser.as_seclang(r))

        with open(f"{APP_BASE}/modsec/conf/config.policy", "w") as f:
            f.write("\n".join(sb))

    def build_keystore(self):
        try:
            os.makedirs(f"{APP_BASE}/keystore")
        except FileExistsError:
            pass

        for c in self.CONFIG["certificates"]:
            with open(f"{APP_BASE}/keystore/{c['_id']}.crt", "w") as f:
                f.write("\n".join([c["certificate"], c["chain"]]))
            with open(f"{APP_BASE}/keystore/{c['_id']}.key", "w") as f:
                f.write(c["private_key"])

    def flush_feeds(self):
        self.build_keystore()
        self.build_crs()

    def build_crs(self):
        ruleset_path = f"{APP_BASE}/modsec/conf"
        policy_file = f"{ruleset_path}/crs.policy"
        sensor_sb = []
        for cat in self.CONFIG["categories"]:
            if "rules" in cat and cat["rules"]:
                for rule in cat["rules"]:
                    if rule and rule["schema_type"] != "SecComponentSignature":
                        try:
                            sensor_sb.append(RuleSetParser.as_seclang(rule, ruleset_path))
                        except Exception as e:
                            logger.error("Failed to parse rule: %s %s", rule, e)
                            stack_trace = traceback.format_exc()
                            logger.error(stack_trace)

        with open(policy_file, "w") as f:
            f.write("\n".join(sensor_sb))

    # noinspection PyListCreation
    def flush_config(self):
        self.flush_feeds()
        clear_directory(f"{APP_BASE}/html")

        os.makedirs(f"{APP_BASE}/cache", exist_ok=True)
        sb = []
        sb.append(f"load_module modules/ngx_http_modsecurity_module.so;")
        sb.append(f"load_module modules/ngx_http_sticky_module.so;")
        sb.append(f"user nproxy nproxy;")
        sb.append(f"pid {APP_BASE}/run/nginx.pid;")
        sb.append(f"events {{worker_connections 1024;}}")

        sb.append("http {")
        sb.append(f" lua_shared_dict geoip_cache 10m;")
        for s in self.CONFIG["sensors"]:
            sb.append(f" lua_shared_dict si_{s['_id']}_cache 10m;")
        sb.append(f" client_body_temp_path {APP_BASE}/temp/client_body;")
        sb.append(f" fastcgi_temp_path {APP_BASE}/temp/fastcgi;")
        sb.append(f" proxy_temp_path {APP_BASE}/temp/proxy;")
        sb.append(f" scgi_temp_path {APP_BASE}/temp/scgi;")
        sb.append(f" uwsgi_temp_path {APP_BASE}/temp/uwsgi;")
        sb.append(" access_log off;error_log /dev/null crit;")
        sb.append(" proxy_intercept_errors on;")
        sb.append(" include mime.types;")
        sb.append(" default_type  application/octet-stream;")
        sb.append(" sendfile on;")
        sb.append(" keepalive_timeout 65;")
        sb.append(f" log_format logger-json escape=json '{self.__LOG_FORMAT}';")
        sb.append(f"large_client_header_buffers 4 32k;")
        self._build_config_policy()

        sb.append(
            " proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;"
        )
        sb.append(
            self.add_upstream(
                {
                    "name": "acme",
                    "retry": 3,
                    "retry_timeout": 300,
                    "protocol": "http",
                    "targets": [{"host": "127.0.0.1", "port": 5000, "weight": 100}],
                }
            )
        )

        if "upstreams" in self.CONFIG:
            for ups in self.CONFIG["upstreams"]:
                sb.append(self.add_upstream(ups))
        sb.append(self.add_monitor())
        sb.append(self.add_mapping())

        for service in self.CONFIG["services"]:
            if "active" in service and service["active"]:
                sb.append(self.add_service(service))

        sb.append("}")

        with open(f"{ENGINE_BASE}/conf/nginx.conf", "w") as f:
            f.write("\n".join(sb))
        return True

    def confirm(self):
        self.CONFIG = self.CONFIG
        self.CONFIG = None

    def add_service(self, service):
        sb = []
        ssl_support=False
        cert=None
        for b in service["bindings"]:
            if b["protocol"] == "HTTPS":
                ssl_support=True
        if "certificate" in service:
            for c in self.CONFIG["certificates"]:
                if c["_id"] == service["certificate"]["_id"]:
                    cert = c
                    break
        if "rate_limit" in service and service["rate_limit"]:
            sb.append(
                f" limit_req_zone $binary_remote_addr zone={service['_id']}_rate:16m rate={service['rate_limit_per_sec']}r/s;"
            )
        sb.append(
            f" proxy_cache_path {APP_BASE}/cache/{service['_id']} keys_zone={service['_id']}_cache:10m use_temp_path=off loader_threshold=300 loader_files=200 max_size=128m;"
        )
        # sb.append(
        #    f" lua_package_cpath '{APP_BASE}/lualib/lib64/lua/5.4/?.so;{APP_BASE}/lualib/lib/?.so;{APP_BASE}/lualib/?.so;;';")
        sb.append(" server {")
        sb.append(f"  lua_code_cache on;")
        # sb.append(f"  expires 1M;")
        server_name = " ".join(list(OrderedDict.fromkeys(service["sans"])))
        sb.append(f"  server_name {server_name};")
        sb.append("  if ($missing_domain_match) {return 410;}")
        if "rate_limit" in service and service["rate_limit"]:
            burst = int(service["rate_limit_per_sec"] * 0.1)
            if burst > 0:
                sb.append(
                    f"  limit_req zone={service['_id']}_rate burst={burst} nodelay;"
                )
            else:
                sb.append(f"  limit_req zone={service['_id']}_rate nodelay;")

        sb.append(f"  set $service_id '{service['_id']}';")
        sb.append(f"  set $upstream_id '-';")
        sb.append(f"  set $route_name '-';")
        sb.append(f"  set $sensor_id '-';")
        sb.append(f"  set $geoip_status '-';")
        sb.append(f"  set $rbl_status '-';")
        sb.append(f"  set $real_method $request_method;")
        


        sb.append(f"  client_max_body_size {service['body_limit']}m;")
        if "compression" in service and service["compression"]:
            sb.append(self.add_compress(service))

        sb.append("  proxy_no_cache $cookie_nocache $arg_nocache$arg_comment;")
        sb.append("  proxy_no_cache $http_pragma    $http_authorization;")

        if service["buffer"] > 0:
            sb.append(f"  proxy_request_buffering on;")
            sb.append(f"  proxy_buffers 8 {service['buffer']}k;")
            sb.append(f"  proxy_buffer_size {service['buffer']}k;")
            sb.append(f"  proxy_busy_buffers_size {service['buffer']}k;")
        else:
            sb.append(f"  proxy_request_buffering off;")
            sb.append(f"  proxy_buffering off;")

        sb.append(f"  add_header X-Request-Id $request_id always;")
        sb.append(f"  add_header X-Server-Id {get_server_id()} always;")
        for header in service["headers"]:
            sb.append(f"  add_header {header['name']} '{header['content']}';")

        sb.append(self.add_service_sensor(service))

        if ssl_support:
            ssl_protocols = " ".join(service["ssl_protocols"])
            sb.append(f"  ssl_protocols {ssl_protocols};")
            sb.append(f"  ssl_prefer_server_ciphers on;")
            sb.append(f"  ssl_session_cache shared:SSL:10m;")
            sb.append(f"  ssl_session_timeout 10m;")
            sb.append(f"  ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK;")
            sb.append(f"  ssl_ecdh_curve secp384r1;")
            sb.append(f"  ssl_stapling on;")
            sb.append(f"  ssl_stapling_verify on;")

            if cert:
                sb.append(f"  ssl_certificate {APP_BASE}/keystore/{cert['_id']}.crt;")
                sb.append(f"  ssl_certificate_key {APP_BASE}/keystore/{cert['_id']}.key;")
                if  cert["provider"] == "MANAGED":
                    sb.append("  location ^~ /.well-known/acme-challenge/ {")
                    sb.append('   default_type "text/plain";')
                    sb.append("   proxy_redirect off;")
                    sb.append("   proxy_pass http://acme;")
                    sb.append(f"   proxy_read_timeout {service['timeout']}s;")
                    sb.append(f"   proxy_connect_timeout {service['timeout']}s;")
                    sb.append(f"   modsecurity_rules '")
                    sb.append(f"    SecRuleRemoveById 920272")
                    sb.append(f"   ';")
                    sb.append("  }")

            if service["ssl_client_auth"]:
                sccf = f"{APP_BASE}/keystore/{service['_id']}.clientssl"
                sb.append(f"  ssl_verify_client optional;")
                sb.append(f"  ssl_verify_depth 5;")
                sb.append(f"  ssl_client_certificate {sccf};")
                sb.append(f"  proxy_set_header X-SSL-Client-Cert $ssl_client_cert;")
                sb.append(f"  proxy_set_header X-SSL-Client-Verify $ssl_client_verify;")
                sb.append(f"  proxy_set_header X-SSL-Protocol $ssl_protocol;")
                sb.append(f"  proxy_set_header X-SSL-Server-Name $ssl_server_name;")

                with open(sccf, "w") as f:
                    f.write(service["ssl_client_ca"])

            sb.append(f"  proxy_ssl_server_name on;")
            sb.append(f"  proxy_ssl_verify off;")

        for b in service["bindings"]:
            if b["protocol"] == "HTTP":
                sb.append(f"  listen {b['port']};")
            if b["protocol"] == "HTTPS":
                sb.append(f"  listen {b['port']} ssl;")
                if "ssl_upgrade" in b and b["ssl_upgrade"]:
                    sb.append(
                        f"  if ($ssl_upgrade) {{return 301 https://$server_name:{b['port']}$request_uri;}}"
                    )
        
        sb.append(self.add_routes(service))

        log_path = f"{APP_BASE}/logs"
        sb.append(f"  access_log {log_path}/access_log-{service['_id']}.log logger-json;")
        sb.append(f"  error_log {log_path}/error_log-{service['_id']}.log;")
        sb.append(f"  error_page 404 403 500 502 503 504 /custom_error;")
        sb.append(f"  location = /custom_error {{")
        sb.append(f"   internal;")
        sb.append(f"   content_by_lua_file {APP_BASE}/lualib/share/lua/5.4/nproxy/content_by_custom_error.lua;")
        sb.append("  }")
        sb.append(" }")
        return "\n".join(sb)

    # noinspection PyListCreation
    def add_service_sensor(self, service):
        ruleset_path = f"{APP_BASE}/modsec/conf"
        config_policy = f"{ruleset_path}/config.policy"
        policy_file = f"{ruleset_path}/service-{service['name']}.policy"

        sb = []
        sb.append(f"  modsecurity on;")
        sb.append(f'  modsecurity_transaction_id "$request_id";')
        sb.append(f"  modsecurity_rules_file {config_policy};")
        sb.append(f"  modsecurity_rules_file {policy_file};")
        sensor_sb = []
        sensor_sb.append("SecAuditEngine On")
        sensor_sb.append(f"SecRequestBodyLimit {service['body_limit'] * 1024 * 1024}")
        sensor_sb.append("SecAuditLogParts ABHF")
        sensor_sb.append("SecAuditLogFormat JSON")
        sensor_sb.append("SecAuditLogType Serial")
        sensor_sb.append("SecDebugLogLevel 0")
        sensor_sb.append(self.add_log(service["_id"], "AUDIT"))
        with open(policy_file, "w") as f:
            f.write("\n".join(sensor_sb))

        sb.append(f"  modsecurity_rules_file {ruleset_path}/crs.policy;")
        return "\n".join(sb)

    def add_log(self, log_id, log_type):
        log_path = f"{APP_BASE}/logs"
        if log_type == "AUDIT":
            return f"SecAuditLog {log_path}/audit_log-{log_id}.log"
        if log_type == "ACCESS_LOG":
            return f"  access_log {log_path}/access_log-{log_id}.log logger-json;"
        if log_type == "ERROR_LOG":
            return f"  error_log {log_path}/error_log-{log_id}.log;"
        return f"# LOG {log_type} NOT SUPPORTED"

    def is_net(self, addr):
        return (
            "/32" not in addr
            and "0.0.0.0" not in addr
            and "/" in addr
            and "127.0.0.0" not in addr
        )

    def add_routes(self, service):
        sb = []
        for route in service["routes"]:
            policy_file = (
                f"{APP_BASE}/modsec/conf/route-{service['name']}-{route['name']}.policy"
            )
            psb = []
            if route["monitor_only"]:
                psb.append("SecRuleEngine DetectionOnly")
            else:
                psb.append("SecRuleEngine On")

            if route["type"] in ["upstream", "static"]:
                psb.append(self.add_route_methods(route))
            sensor = None
            if "sensor" in route:
                for s in self.CONFIG["sensors"]:
                    if s["_id"] == route["sensor"]["_id"]:
                        sensor = copy.deepcopy(s)
                        break
                r10 = SecAction().load(
                    {
                        "schema_type": "SecAction",
                        "phase": 1,
                        "code": 10,
                        "action": "pass",
                        "t": ["none"],
                        "logging": "nolog",
                        "setvar": [
                            f"tx.sensor_level={sensor['inspect_level']}",
                            f"tx.sensor_iscore={sensor['inbound_score']}",
                            f"tx.sensor_oscore={sensor['outbound_score']}",
                        ],
                        "order": 1,
                    }
                )
                psb.append(RuleSetParser.as_seclang(r10))
                exclusions = []
                if "exclusions" in sensor:
                    exclusions = sensor["exclusions"]

                for cat in self.CONFIG["categories"]:
                    if cat["name"] not in sensor["categories"] and cat["phase"] in [
                        3,
                        5,
                    ]:
                        for rule in cat["rules"]:
                            if rule["schema_type"] == "SecRule":
                                exclusions.append(rule["code"])
                exclude_sub = [
                    exclusions[i : i + 10] for i in range(0, len(exclusions), 10)
                ]
                for idx, exclude_sub in enumerate(exclude_sub):
                    exclude_list = " ".join(map(str, exclude_sub))
                    psb.append(f"SecRuleRemoveById {exclude_list}")

            with open(policy_file, "w") as f:
                f.write("\n".join(psb))

            for path in route["paths"]:
                is_regex = path.startswith("^")
                if is_regex:
                    sb.append(f"  location ~ {path}{{")
                else:
                    sb.append(f"  location {path}{{")

                if sensor:
                    sb.append(f"   set $sensor_id '{route['sensor']['_id']}';")
                    sb.append(f"   set $route_name '{route['name']}';")

                    sb.append(f"   set $api_url 'http://127.0.0.1:5000/api';")
                    sb.append(f"   set $api_key {NODE_KEY};")
                    if "geo_block_list" in sensor:
                        sb.append(
                            f"   set $geo_block_list '{'|'.join(sensor['geo_block_list'])}';"
                        )
                    sb.append(
                        f"   access_by_lua_file  {APP_BASE}/lualib/share/lua/5.4/nproxy/deny_by_sensor.lua;"
                    )
                else:
                    sb.append(f"   set $sensor_id '-';")

                if "filters" in route:
                    for f in route["filters"]:
                        if "SSL_CLIENT_AUTH" in f["type"]:
                            sb.append(
                                "   if ($ssl_client_verify != SUCCESS) {return 403;}"
                            )
                            # sb.append("   if ($ssl_client_i_dn !~ '" +f['ssl_dn_regex']+"')  {return 403;}")

                        if "LDAP_BASIC_AUTH" in f["type"]:
                            sb.append(f"   set $ldap_host \"{f['ldap_host']}\";")
                            sb.append(f"   set $ldap_base_dn \"{f['ldap_base_dn']}\";")
                            sb.append(f"   set $ldap_bind_dn \"{f['ldap_bind_dn']}\";")
                            sb.append(
                                f"   set $ldap_bind_password \"{f['ldap_bind_password']}\";"
                            )
                            if "ldap_group_dn" in f:
                                sb.append(
                                    f"   set $ldap_group_dn \"{f['ldap_group_dn']}\";"
                                )
                            sb.append(
                                f"   access_by_lua_file {APP_BASE}/lualib/share/lua/5.4/nproxy/access_by_ldap_auth.lua;"
                            )

                sb.append(f"   modsecurity_rules_file {policy_file};")

                if route["type"] in ["redirect"]:
                    sb.append(
                        f"   return {route['redirect']['code']} {route['redirect']['url']};"
                    )

                if route["type"] in ["upstream", "static"]:
                    ups = None
                    for u in self.CONFIG["upstreams"]:
                        if u["_id"] == route["upstream"]["_id"]:
                            ups = u
                            break
                    sb.append(f"   set $upstream_id '{route['upstream']['_id']}';")

                    if "static" in ups["type"]:
                        logger.debug(
                            f"Deploy static {len(ups['content'])} to {APP_BASE}/html/{ups['name']}"
                        )
                        unpack_zip(ups["content"], f"{APP_BASE}/html/{ups['name']}")
                        sb.append(f"   root {APP_BASE}/html/{ups['name']};")
                        sb.append(f"   index {ups['index']};")

                    if "backend" in ups["type"]:
                        sb.append(f"   proxy_http_version 1.1;")
                        sb.append(f"   proxy_intercept_errors on;")
                        sb.append(
                            f"   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
                        )
                        sb.append(f"   proxy_read_timeout {service['timeout']}s;")

                        # real-ip
                        sb.append(f"   proxy_set_header Host $host;")
                        sb.append(f"   proxy_set_header X-Real-IP $remote_addr;")

                        # websocket
                        sb.append(f"   proxy_set_header Upgrade $http_upgrade;")
                        sb.append(
                            f"   proxy_set_header Connection $connection_upgrade;"
                        )

                        if "http" in ups["protocol"].lower():
                            if is_regex:
                                sb.append(f"   proxy_redirect off;")
                                sb.append(
                                    f"   proxy_pass {ups['protocol'].lower()}://{ups['name']}/$1$is_args$args;"
                                )
                            else:
                                sb.append(
                                    f"   proxy_redirect {ups['protocol'].lower()}://{ups['name']}/ {ups['protocol'].lower()}://$host/;"
                                )
                                sb.append(
                                    f"   proxy_pass {ups['protocol'].lower()}://{ups['name']};"
                                )

                        elif "cgi" in ups["protocol"].lower():
                            sb.append(f"   include fastcgi.conf;")
                            sb.append(f"   include fastcgi_params;")
                            sb.append(
                                f"   fastcgi_param SCRIPT_FILENAME {ups['script_path']}$fastcgi_script_name;"
                            )
                            sb.append(f"   fastcgi_pass {ups['name']};")
                        elif "ajp" in ups["protocol"].lower():
                            sb.append(f"   ajp_keep_conn on;")
                            sb.append(f"   ajp_pass {ups['name']};")

                sb.append("  }")
        return "\n".join(sb)

    def mapping_exists(self, sb, cn):
        if cn in sb:
            return True
        return False

    def add_mapping(self):
        h_list = []
        for service in self.CONFIG["services"]:
            if "sans" in service:
                h_list.extend(service["sans"])

        sb = [" map $host $missing_domain_match {"]
        for h in list(OrderedDict.fromkeys(h_list)):
            sb.append(f"  {h} 0;")

        sb.append("  default 1;")
        sb.append(" }")
        sb.append(" map $http_upgrade $connection_upgrade {default upgrade;'' close;}")

        sb.append(" map '$scheme:$request_uri' $ssl_upgrade{")
        sb.append(r"  ~^http:/\.well-known/acme-challenge/ 0;")
        sb.append(r"  ~^http: 1;")
        sb.append(f"  default 0;")
        sb.append(" }")

        return "\n".join(sb)

    def add_upstream(self, upstream):
        sb = []

        if "targets" in upstream and len(upstream["targets"]) > 0:
            sb.append(f" upstream {upstream['name']} {{ ")
            logger.debug(
                f" connection refused with type={upstream['protocol'].lower()}"
            )
            sb.append(
                f"  check interval=5000 fall={upstream['retry']} rise=1 default_down=true type=tcp;"
            )
            if upstream["protocol"] == "HTTP":
                sb.append(
                    '  check_http_send "HEAD / HTTP/1.0\\r\\n\\r\\n\\r\\n\\r\\n";'
                )
                sb.append("  check_http_expect_alive http_2xx http_3xx http_4xx;")

            if "persist" in upstream and upstream["persist"]["type"] == "COOKIE":
                if "cookie_name" in upstream["persist"]:
                    cookie_name = upstream["persist"]["cookie_name"]
                else:
                    cookie_name = "x_lb"
                if "cookie_path" in upstream["persist"]:
                    cookie_path = upstream["persist"]["cookie_path"]
                else:
                    cookie_path = "/"
                sb.append(f"  sticky name={cookie_name} path={cookie_path} hash=md5;")

            valid_servers = []
            for t in upstream["targets"]:
                host = t['host']
                # Try to resolve hostname if it's not an IP address
                if not NetworkTool.is_host(host):
                    resolved_ip = NetworkTool.hostbyname(host)
                    if resolved_ip:
                        host = resolved_ip
                    else:
                        logger.warning(f"Skipping server configuration for unresolvable hostname {host}")
                        continue
                
                valid_servers.append(
                    f"  server {host}:{t['port']} max_fails={upstream['retry']} weight={t['weight']} fail_timeout={upstream['retry_timeout']};"
                )

            if not valid_servers:
                logger.warning(f"No valid servers found for upstream {upstream['name']}, adding default server")
                valid_servers.append(
                    f"  server 127.0.0.1:65535 down; # Default server when no valid targets found"
                )

            sb.extend(valid_servers)
            sb.append(f" }}")

        return "\n".join(sb)

    def add_compress(self, service=None):
        sb = [
            "  gzip on;",
            "  gzip_min_length 1000;",
            "  gzip_disable 'msie6';",
            "  gzip_proxied no-cache no-store expired;",
        ]
        if service and "compression_types" in service:
            sb.append(f"  gzip_types {' '.join(service['compression_types'])};")
        return "\n".join(sb)

    # noinspection PyListCreation
    def add_monitor(self):
        sb = []
        sb.append(" server {")
        sb.append("  server_name 127.0.0.1;")
        sb.append(f"  listen 5001;")
        sb.append(f"  set $service_id 'monitor';")
        sb.append(f"  set $upstream_id '-';")
        sb.append(f"  set $route_name '-';")
        sb.append(f"  set $sensor_id '-';")
        sb.append(f"  set $geoip_status '-';")
        sb.append(f"  set $rbl_status '-';")

        sb.append("  access_log off;error_log /dev/null crit;")
        sb.append("  location /ngx_up_status {")
        sb.append("   add_header Content-Type application/json;")
        sb.append("   allow 127.0.0.1;deny all;")
        sb.append("   check_status json;")
        sb.append("  }")
        sb.append("  location /ngx_status {")
        sb.append("   stub_status  on; allow 127.0.0.1;deny all;")
        sb.append("   add_header Content-Type application/json;")
        sb.append(
            '   return 200 \'{"active": $connections_active,"waiting": $connections_waiting}\';'
        )
        sb.append("  }")
        sb.append("}")
        return "\n".join(sb)

    def add_route_methods(self, route):
        sb = []
        methods = " ".join(method for method in route["methods"])
        r11 = SecAction().load(
            {
                "schema_type": "SecAction",
                "phase": 1,
                "code": 11,
                "action": "pass",
                "t": ["none"],
                "logging": "nolog",
                "setvar": [f"tx.route_methods={methods}"],
            }
        )
        sb.append(RuleSetParser.as_seclang(r11))

        r12 = SecRule().load(
            {
                "schema_type": "SecRule",
                "code": 12,
                "phase": 1,
                "action": "deny",
                "logging": "log",
                "logdata": "'%{MATCHED_VAR}'",
                "audit_log": "auditlog",
                "scope": ["REQUEST_METHOD"],
                "condition": "!@within %{tx.route_methods}",
                "msg": "'Method is not allowed by route'",
                "severity": "'CRITICAL'",
            }
        )
        sb.append(RuleSetParser.as_seclang(r12))
        return "\n".join(sb)
