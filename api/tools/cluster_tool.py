import os
import pickle
import socket
import subprocess
import traceback
from datetime import datetime, timedelta

import psutil
import requests

from api.common_utils import logger, get_server_id, API_HEADERS
from api.model.config_model import ConfigDao
from api.model.telemetry_model import TelemetryTrnDao
from api.model.transaction_model import TransactionDao
from api.model.upstream_model import UpstreamDao, NodeStatusDao
from api.tools.engine_tool import EngineManager
from api.tools.network_tool import NetworkTool
from api.tools.service_watcher import ServiceWatcher
from config import (
    APP_BASE,
    ENGINE_VERSION,
    NODE_ROLE,
    TZ,
    TELEMETRY_URL,
)


class ClusterTool:
    CONFIG = None
    service_watchers = []

    @classmethod
    def check_tcp_port(cls, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, int(port)))
            return result == 0
        except Exception as e:
            logger.warn("Starting as main %s", e)
            return False

    @classmethod
    def auto_flush_feeds(cls):
        try:
            manager = EngineManager()
            if manager.CONFIG:
                if not cls.CONFIG or manager.CONFIG["scn"] not in cls.CONFIG["scn"]:
                    logger.info(
                        f"Flush feeds {cls.CONFIG['scn']} -> {manager.CONFIG['scn']}"
                    )
                    cls.CONFIG.update(
                        {
                            "scn": manager.CONFIG["scn"],
                            "certificates": manager.CONFIG["certificates"],
                            "feeds": manager.CONFIG["feeds"],
                            "categories": manager.CONFIG["categories"],
                            "jails": manager.CONFIG["jails"],
                        }
                    )
                    manager.flush_feeds()
                    cls.restart()

        except Exception:
            stack_trace = traceback.format_exc()
            logger.error(f"Error executing command: {stack_trace}")

    @classmethod
    def send_telemetry(cls):
        dao = TelemetryTrnDao()
        result = dao.get_by_logtime(datetime.now(TZ) - timedelta(hours=24))
        if result:
            cdao = ConfigDao()
            c = cdao.get_active()
            tlm = {
                "cluster_id": c["cluster_id"],
                "net_recv": result[0]["net_recv"],
                "net_send": result[0]["net_send"],
                "req_total": result[0]["req_total"],
                "latency": result[0]["latency"],
            }
            try:
                response = requests.post(
                    f"{TELEMETRY_URL}/api/usage",
                    json=tlm,
                    headers=API_HEADERS,
                    timeout=10,
                )
                if response.status_code in [200, 201]:
                    logger.info(response.status_code)
                else:
                    logger.warn(
                        f"Failed with code {response.status_code}, disable with TELEMETRY_ENABLE=false"
                    )
            except Exception as e:
                logger.error(f"Failed to send telemetry {e}")

    @classmethod
    def collect_telemetry(cls):
        dao = TransactionDao()
        tl_dao = TelemetryTrnDao()
        trn_telemetry = dao.get_trn_telemetry(datetime.now(TZ))
        if trn_telemetry:
            for ct in trn_telemetry:
                tl_dao.persist(ct)
        else:
            tl_dao.persist(
                {
                    "net_recv": 0,
                    "net_send": 0,
                    "req_total": 0,
                    "latency": 0.0,
                    "logtime": datetime.now(TZ),
                    "server_id": get_server_id(),
                }
            )

    @classmethod
    def auto_replicate_config(cls):
        manager = EngineManager()
        if manager.CONFIG:
            if not cls.CONFIG or manager.CONFIG["scn"] not in cls.CONFIG["scn"]:
                r_st = manager.flush_config()
                if r_st:
                    logger.info(
                        f"Replicate {cls.CONFIG['scn']} -> {manager.CONFIG['scn']}"
                    )
                    cls.CONFIG = manager.CONFIG
                    cls.restart(fully=True)

    @classmethod
    def __eval_upstream(cls, upstream, ngx_status):
        status = {"_id": upstream["_id"], "name": upstream["name"], "targets": []}
        for t in upstream["targets"]:
            target = {"healthy": False}
            try:
                target.update({"endpoint": f"{t['host']}:{t['port']}"})
                if not NetworkTool.is_host(t["host"]):
                    target.update(
                        {"endpoint": f"{NetworkTool.hostbyname(t['host'])}:{t['port']}"}
                    )
                for s in ngx_status["servers"]["server"]:
                    if (
                        s["name"] == target["endpoint"]
                        and s["upstream"] == upstream["name"]
                    ):
                        target.update({"healthy": ("UP" in s["status"].upper())})
                        if not target["healthy"]:
                            logger.warn(
                                f"Endpoint {upstream['name']}->{target['endpoint']} healthy {target['healthy']} on {get_server_id()}"
                            )
                        logger.debug(
                            f" {s['name']} == {target['endpoint']} and  {s['upstream']}=={upstream['name']} = {s['status'].upper()}"
                        )
            except Exception:
                stack_trace = traceback.format_exc()
                logger.error(stack_trace)

            target.update({"endpoint": f"{t['host']}:{t['port']}"})
            status["targets"].append(target)
        return status

    @classmethod
    def node_monitor(cls):
        dao_st = NodeStatusDao()
        model = UpstreamDao()
        try:
            node_st = dao_st.get_by_name(get_server_id())
            if not node_st:
                node_st = {"name": get_server_id(), "upstreams": []}
                pk = dao_st.persist(node_st)
                node_st.update({"_id": pk})
            node_st.update(
                {
                    "version": ENGINE_VERSION,
                    "role": NODE_ROLE,
                    "last_check": datetime.now(),
                }
            )

            if cls.CONFIG:
                node_st.update({"scn": cls.CONFIG["scn"]})
            upstreams = model.get_all_by_type("backend")
            if len(upstreams) > 0:
                response = requests.get("http://127.0.0.1:9000/ngx_up_status")
                if response.status_code == 200:
                    ngx_status = response.json()
                    node_st["upstreams"] = []
                    for u in upstreams:
                        ups = cls.__eval_upstream(u, ngx_status)
                        node_st["upstreams"].append(ups)
                else:
                    logger.error(
                        f"Monitor error [{response.status_code}] {response.text}"
                    )
            dao_st.update_by_id(node_st["_id"], node_st)
            return node_st
        except Exception as e:
            # stack_trace = traceback.format_exc()
            # logger.error(stack_trace)
            logger.error(f"Check failed {e}")

    @classmethod
    def stop_log_monitor(cls):
        for t in cls.service_watchers:
            t.stop()
        cls.service_watchers = []

    @classmethod
    def start_log_monitor(cls):
        manager = EngineManager()
        if "services" in manager.CONFIG:
            for service in manager.CONFIG["services"]:
                watcher = ServiceWatcher(service)
                cls.service_watchers.append(watcher)

            for w in cls.service_watchers:
                w.start()

    @classmethod
    def is_running(cls):
        pid_file = f"{APP_BASE}/run/nginx.pid"
        try:
            if os.path.exists(pid_file):
                with open(pid_file, "r") as file:
                    pid = int("".join(file.readlines()))
                    if pid:
                        process = psutil.Process(pid)
                        is_running = process.is_running()
                        if not is_running:
                            os.remove(pid_file)
                        return is_running
        except Exception as e:
            logger.error("Failed to check engine, %s", e)
        return False

    @classmethod
    def restart(cls, fully=False):
        if fully:
            cls.stop_log_monitor()

        cls.run = subprocess.run(f"sudo chmod -R 777 {APP_BASE}/logs", shell=True)
        if cls.is_running():
            logger.info(f"Nginx is running, reload required")
            result = subprocess.Popen(
                f"sudo {EngineManager.nginx} -s reload",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if not cls.is_running():
                logger.info(f"Nginx reload failed, start required")
                result = subprocess.Popen(
                    f"sudo {EngineManager.nginx}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
        else:
            logger.info(f"Nginx is not running, start required")
            result = subprocess.Popen(
                f"sudo {EngineManager.nginx}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        stdout, stderr = result.communicate()
        cls.run = subprocess.run(f"sudo chmod -R 777 {APP_BASE}/logs", shell=True)
        if result.returncode == 0:
            if fully:
                cls.start_log_monitor()
            return {"succeed": True}
        else:
            return {"succeed": False, "message": stderr.decode()}

    @classmethod
    def apply_config(cls, reconfigure=False):
        logger.info(f"Start on {get_server_id()}")
        try:
            manager = EngineManager()
            if reconfigure:
                manager.flush_config()
                restart_result = cls.restart(fully=True)
            else:
                restart_result = cls.restart()
            if restart_result["succeed"]:
                cls.CONFIG = manager.CONFIG
                logger.info(f"Engine active with scn {cls.CONFIG['scn']}")
                with open(f"{APP_BASE}/run/activated.config", "wb") as f:
                    pickle.dump(cls.CONFIG, f)  # SAVE START_CONFIG
            else:
                logger.error(f"Engine failed, {restart_result['message']}")
            return restart_result
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"Error executing command: {stack_trace}")
            return {"succeed": False, "message": str(e), "details": stack_trace}
