import traceback
from datetime import datetime, timedelta

# noinspection PyPep8Naming
from acme import errors as ACMEerrors

from common_utils import logger, replace_tz
from model.acme_model import ChallengeDao
from model.certificate_model import CertificateDao
from model.service_model import ServiceDao
from tools.cluster_tool import ClusterTool
from tools.ssl_tool import SSLLetsEncryptTool, SSLTool


class AcmeTool:
    __CERTIFICATE_RENEW = 7

    @classmethod
    def clean_expired_challenges(cls):
        dao = ChallengeDao()
        dao.delete_issued_before(
            datetime.now() + timedelta(days=cls.__CERTIFICATE_RENEW)
        )

    @classmethod
    def renew_self(cls, certificate):
        dao = ServiceDao()
        ca = None
        if ClusterTool.CONFIG:
            ca = {
                "certificate": SSLTool.crt_from_pem(ClusterTool.CONFIG['config']['ca_certificate']),
                "private_key": SSLTool.private_from_pem(ClusterTool.CONFIG['config']['ca_private']),
            }

        services = dao.getall_by_certificate_id(certificate["_id"])

        cn = None
        sans = []
        for s in services:
            if not cn:
                cn = s["sans"][0]
                sans = s["sans"][1:]
            else:
                sans.extend(s["sans"])

        self_crt = SSLTool.create_certificate(cn, sans=list(set(sans)), ca=ca)
        self_chain = []
        for c in self_crt["chain"]:
            self_chain.append(SSLTool.crt_to_pem(c))
        crt = {
            "name": certificate["name"],
            "provider": certificate["provider"],
            "chain": "\n".join(self_chain),
            "certificate": SSLTool.crt_to_pem(self_crt["certificate"]),
            "private_key": SSLTool.private_to_pem(self_crt["private_key"]),
            "subjects": self_crt["subjects"],
            "not_before": self_crt["not_before"],
            "not_after": self_crt["not_after"],
            "force_renew": "MANAGED" == certificate["provider"],
        }
        crt.update(SSLTool.extract_info_from_crt(self_crt["certificate"]))
        CertificateDao().update_by_id(certificate["_id"], crt)

    @classmethod
    def renew_lets(cls, certificate):
        dao = ServiceDao()
        try:
            services = dao.getall_by_certificate_id(certificate["_id"])
            cn = None
            sans = []
            for s in services:
                if cn:
                    sans.extend(s["sans"])
                else:
                    cn = s["sans"][0]
                    sans = s["sans"][1:]

            result = SSLLetsEncryptTool.create_certificate(
                cn, sans=sans, email="fake@tooka.com.br"
            )
            if result:
                chain_list = []
                for c in result["chain"]:
                    c_pem = SSLTool.crt_to_pem(c)
                    chain_list.append(c_pem)
                chain = "\n".join(chain_list)
                certificate.update(
                    {
                        "chain": chain,
                        "certificate": SSLTool.crt_to_pem(result["certificate"]),
                        "private_key": SSLTool.private_to_pem(result["private_key"]),
                        "status": "VALID",
                        "force_renew": False,
                    }
                )

                certificate.update(SSLTool.extract_info_from_crt(result["certificate"]))
                CertificateDao().update_by_id(certificate["_id"], certificate)
        except ACMEerrors.ValidationError as e:
            for rs in e.failed_authzrs:
                for challenge in rs.body.challenges:
                    logger.error(challenge.error)

    @classmethod
    def auto_renew(cls):
        if ClusterTool.CONFIG:
            cls.clean_expired_challenges()
            dao_service = ServiceDao()
            services = dao_service.get_all()
            crt_count = 0
            if "data" in services:
                for service in services["data"]:
                    if "certificate" in service:
                        renew_date = datetime.now() - timedelta(
                            days=cls.__CERTIFICATE_RENEW
                        )
                        renew_date = replace_tz(renew_date)
                        certificate = service["certificate"]
                        if (
                            certificate["force_renew"] == True
                            or replace_tz(certificate["not_after"]) < renew_date
                        ):
                            try:
                                if "MANAGED" in certificate["provider"]:
                                    cls.renew_lets(certificate)
                                if "SELF" in certificate["provider"]:
                                    cls.renew_self(certificate)
                                crt_count += 1
                            except Exception as e:
                                stack_trace = traceback.format_exc()
                                logger.error(f"{e}, {stack_trace}")
                logger.info(f"{crt_count} certificate renewed")
            return crt_count
