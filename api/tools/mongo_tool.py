import os
import shutil
import zipfile

from model.certificate_model import CertificateDao
from model.feed_model import FeedDao
from model.geoip_model import GeoIpDao
from model.oauth_model import UserDao
from model.seclang_model import RuleCategoryDao, RuleDao
from model.sensor_model import SensorDao
from model.service_model import ServiceDao
from model.upstream_model import UpstreamDao
from config import APP_BASE


class MongoTool:

    @classmethod
    def backup(cls):
        if not os.path.exists(f"{APP_BASE}/backup"):
            os.makedirs(f"{APP_BASE}/backup")
        UserDao().data_export(f"{APP_BASE}/backup")
        CertificateDao().data_export(f"{APP_BASE}/backup")
        GeoIpDao().data_export(f"{APP_BASE}/backup")
        RuleCategoryDao().data_export(f"{APP_BASE}/backup")
        RuleDao().data_export(f"{APP_BASE}/backup")
        SensorDao().data_export(f"{APP_BASE}/backup")
        UpstreamDao().data_export(f"{APP_BASE}/backup")
        ServiceDao().data_export(f"{APP_BASE}/backup")
        FeedDao().data_export(f"{APP_BASE}/backup")

        with zipfile.ZipFile(
            f"{APP_BASE}/backup.zip", "w", zipfile.ZIP_DEFLATED
        ) as z_ipf:
            for root, _, files in os.walk(f"{APP_BASE}/backup"):
                for file in files:
                    file_path = os.path.join(root, file)
                    z_ipf.write(
                        file_path, os.path.relpath(file_path, f"{APP_BASE}/backup")
                    )
            shutil.rmtree(f"{APP_BASE}/backup")
            return f"{APP_BASE}/backup.zip"

    @classmethod
    def restore(cls, zip_path):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(f"{APP_BASE}/backup")

        UserDao().data_import(f"{APP_BASE}/backup")
        CertificateDao().data_import(f"{APP_BASE}/backup")
        GeoIpDao().data_import(f"{APP_BASE}/backup")
        RuleCategoryDao().data_import(f"{APP_BASE}/backup")
        RuleDao().data_import(f"{APP_BASE}/backup")
        SensorDao().data_import(f"{APP_BASE}/backup")
        UpstreamDao().data_import(f"{APP_BASE}/backup")
        ServiceDao().data_import(f"{APP_BASE}/backup")
        FeedDao().data_import(f"{APP_BASE}/backup")
        os.remove(zip_path)
        shutil.rmtree(f"{APP_BASE}/backup")
