import threading

from common_utils import LogCache, logger
from tools.log_tool import LogParserTool
from config import APP_BASE


class ServiceWatcher:
    def __init__(self, service):
        self.service = service
        self.w_threads = []
        self.cache = LogCache()

    def stop(self):
        logger.info(f"[stop] {self.service['name']}")
        for t in self.w_threads:
            t.active = False

        for t in self.w_threads:
            t.join()

    def start(self):
        logger.info(f"[start] {self.service['name']}")
        cache = LogCache()
        access_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                cache,
                f"{APP_BASE}/logs/access_log-{self.service['name']}.log",
                "ACCESS",
            ),
            daemon=False,
        )
        self.w_threads.append(access_log)

        error_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                cache,
                f"{APP_BASE}/logs/error_log-{self.service['name']}.log",
                "ERROR",
            ),
            daemon=False,
        )
        self.w_threads.append(error_log)

        audit = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                cache,
                f"{APP_BASE}/logs/audit_log-{self.service['name']}.log",
                "AUDIT",
            ),
            daemon=False,
        )
        self.w_threads.append(audit)

        merge = threading.Thread(
            target=LogParserTool.merge_transactions,
            args=(
                cache,
                self.service["name"],
            ),
            daemon=False,
        )
        self.w_threads.append(merge)
        for thread in self.w_threads:
            thread.start()
