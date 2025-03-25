import os
import threading
import time
import traceback
from xmlrpc.client import boolean

import schedule
from flask import Flask, render_template, send_from_directory, Blueprint
from flask_cors import CORS
from flask_restful import Api

from api.common_utils import ma, socketio, ResponseBuilder, gen_random_string
from api.controller.certificate_controller import routes as certificate_routes
from api.controller.challenge_controller import routes as acme_routes
from api.controller.cluster_controller import routes as cluster_routes
from api.controller.dictionary_controller import routes as dictionary_routes
from api.controller.feed_controller import routes as feed_routes
from api.controller.health_controller import routes as health_routes
from api.controller.jail_controller import routes as jail_routes
from api.controller.oauth_controller import routes as oauth_routes
from api.controller.replica_controller import routes as replica_routes
from api.controller.route_filter_controller import routes as route_filter_routes
from api.controller.rulecat_controller import routes as rule_cat_routes
from api.controller.rulesec_controller import routes as rule_sec_routes
from api.controller.sensor_controller import routes as sensor_routes
from api.controller.service_controller import routes as service_routes
from api.controller.transaction_controller import routes as trn_routes
from api.controller.upstream_controller import routes as upstream_routes
from api.controller.user_controller import routes as user_routes
from api.model.config_model import ConfigDao
from api.tools.acme_tool import AcmeTool
from api.tools.archive_tool import LogArchiverTool
from api.tools.cluster_tool import ClusterTool
from api.tools.feed_tool import RuleSetTool, JailTool
from api.tools.feed_tool import SecurityFeedTool
from cli import install
from config import APP_BASE, NODE_ROLE, MAINTENANCE_WINDOW, TELEMETRY_ENABLE, TELEMETRY_INTERVAL

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB

bp = Blueprint("gw", __name__, template_folder="templates")

cors = CORS(resources={r"/*": {"origins": "*"}})
cors.init_app(app)

ma.init_app(app)
socketio.init_app(app)
api = Api(app)

@app.errorhandler(404)
def not_found_error(error):
    return ResponseBuilder.error_404()


@app.errorhandler(500)
def internal_error(error):
    stack_trace = traceback.format_exc()
    app.logger.error(f"500 Error: {error}, Stack Trace: {stack_trace}")
    return ResponseBuilder.error_500("Unexpected Server Error", details=stack_trace)


@app.errorhandler(Exception)
def handle_exception(error):
    stack_trace = traceback.format_exc()
    app.logger.error(f"Internal Server Error: {stack_trace}")
    return ResponseBuilder.error_500("Unexpected Server Error", details=stack_trace)


@bp.route("/")
def index():
    return render_template('index.html')


@bp.route("/<path:path>")
def catch_all(path):
    static_files_dir = "./static"
    _path = path.lower().strip()
    if path in ["", "/", None]:
        return render_template('index.html')
    elif _path.endswith(".css"):
        return send_from_directory(static_files_dir, path, mimetype="text/css")
    elif _path.endswith(".js"):
        return send_from_directory(static_files_dir, path, mimetype="application/javascript")
    elif "." in _path:
        return send_from_directory(static_files_dir, path)
    else:
        return render_template('index.html')


app.register_blueprint(bp)
routes = [
    (user_routes, "/api/user"),
    (upstream_routes, "/api/upstream"),
    (rule_cat_routes, "/api/rulecat"),
    (rule_sec_routes, "/api/rulesec"),
    (dictionary_routes, "/api/dictionary"),
    (feed_routes, "/api/feed"),
    (certificate_routes, "/api/certificate"),
    (sensor_routes, "/api/sensor"),
    (service_routes, "/api/service"),
    (cluster_routes, "/api/cluster"),
    (replica_routes, "/api/replica"),
    (trn_routes, "/api/trn"),
    (jail_routes, "/api/jail"),
    (route_filter_routes, "/api/route_filter"),
    (acme_routes, "/.well-known"),
    (health_routes, "/health"),
    (oauth_routes, "/api/oauth"),
]
for route, url_prefix in routes:
    app.register_blueprint(route, url_prefix=url_prefix)

def _scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            app.logger.error(f"Error running scheduled task: {e}")
        time.sleep(1)


with app.app_context():
    if not os.path.exists(f"{APP_BASE}/logs"):
        os.makedirs(f"{APP_BASE}/logs")

    dao = ConfigDao()
    config = dao.get_active()

    if "main" in NODE_ROLE:
        if not config:
            app.logger.info("App not installed, starting installation process.")
            install()
            config = dao.get_active()
        if "cluster_id" not in config:
            dao.update_by_id(config['_id'],{"cluster_id": f"{gen_random_string(64)}"})

        schedule.every().day.at(MAINTENANCE_WINDOW).do(RuleSetTool.update)
        schedule.every().day.at(MAINTENANCE_WINDOW).do(SecurityFeedTool().update)
        schedule.every().day.at(MAINTENANCE_WINDOW).do(AcmeTool.auto_renew)
        schedule.every(60).seconds.do(LogArchiverTool.auto_archive)
        schedule.every(10).seconds.do(JailTool.calc_process_jails)
        schedule.every(10).seconds.do(ClusterTool.auto_flush_feeds)
        if boolean(TELEMETRY_ENABLE):
            app.logger.info(f"Telemetry is enabled, thanks for helping our community.")
            schedule.every().day.at(MAINTENANCE_WINDOW).do(ClusterTool.send_telemetry)
            schedule.every(int(TELEMETRY_INTERVAL)).minutes.do(ClusterTool.collect_telemetry)
    else:
        schedule.every(10).seconds.do(ClusterTool.auto_replicate_config)
    schedule.every(10).seconds.do(ClusterTool().node_monitor)

    try:
        ClusterTool.apply_config(reconfigure=True)
        if "main" in NODE_ROLE:
            AcmeTool.auto_renew()
            if boolean(TELEMETRY_ENABLE):
                ClusterTool.collect_telemetry()
                ClusterTool.send_telemetry()
    except Exception as e:
        app.logger.error(f"Failed to apply configuration: {e}")
        app.logger.error(traceback.format_exc())

    app.logger.info(f"System is up and running")
    scheduler_thread = threading.Thread(target=_scheduler, daemon=True)
    scheduler_thread.start()