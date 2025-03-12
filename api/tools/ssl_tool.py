import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta

import josepy as jose
from acme import challenges, client, crypto_util, messages
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509.oid import NameOID

from api.common_utils import logger, replace_tz
from api.model.acme_model import ChallengeDao
from api.model.config_model import ConfigDao
from config import APP_BASE, KEY_SIZE, ENGINE_BASE, TZ


class SSLTool:
    @classmethod
    def private_from_pem(cls, pem, password=None):
        return serialization.load_pem_private_key(pem.encode(), password=password)

    @classmethod
    def private_to_pem(cls, pk):
        return pk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")

    @classmethod
    def crt_to_pem(cls, crt):
        return crt.public_bytes(encoding=serialization.Encoding.PEM).decode("ascii")

    @classmethod
    def crt_from_pem(cls, pem) -> x509.Certificate:
        return x509.load_pem_x509_certificate(pem.encode(), default_backend())

    @classmethod
    def generate_private_key(cls):
        return rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)

    @classmethod
    def gen_csr(cls, domain_names, pk):
        pk_bytes = pk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return crypto_util.make_csr(pk_bytes, domain_names)

    @classmethod
    def gen_ca(cls, crt_cn, crt_org=None):
        ca_key = cls.generate_private_key()
        curr_date = datetime.now().astimezone(TZ)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "SaoPaulo"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "SaoPaulo"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, crt_org),
                x509.NameAttribute(NameOID.COMMON_NAME, crt_cn),
            ]
        )

        ca_crt = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(curr_date)
            .not_valid_after(curr_date + timedelta(days=3650))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .sign(private_key=ca_key, algorithm=SHA256(), backend=default_backend())
        )
        return {
            "certificate": ca_crt,
            "private_key": ca_key,
        }

    @classmethod
    def create_certificate(cls, domain, sans=None, email="fake@tooka.com.br", ca=None):
        if not ca:
            ca = cls.gen_ca("Internal", crt_org="Tooka-Internal")
        curr_date = datetime.now().astimezone(TZ)
        server_key = cls.generate_private_key()

        if sans:
            san_list = [x509.DNSName(c) for c in list(set(sans))]
        else:
            san_list =[]

        logger.info(f"Create certificate for {domain} with {sans}")

        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "SaoPaulo"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "SaoPaulo"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Tooka-Internal"),
                x509.NameAttribute(NameOID.COMMON_NAME, domain),
            ]
        )

        server_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca["certificate"].subject)
            .public_key(server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(curr_date)
            .not_valid_after(curr_date + timedelta(days=365))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
            .sign(
                private_key=ca["private_key"],
                algorithm=SHA256(),
                backend=default_backend(),
            )
        )

        certificate_dict = {
            "chain": [ca["certificate"]],
            "certificate": server_cert,
            "private_key": server_key,
        }
        certificate_dict.update(SSLTool.extract_info_from_crt(server_cert))
        return certificate_dict

    @classmethod
    def extract_info_from_crt(cls, crt):
        subjects = []
        for c in crt.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME):
            subjects.append(c.value)
        for c in crt.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
        ).value:
            subjects.append(c.value)

        return {
            "subjects": list(OrderedDict.fromkeys(subjects)),
            "not_before": replace_tz(crt.not_valid_before).replace(microsecond=0),
            "not_after": replace_tz(crt.not_valid_after).replace(microsecond=0),
        }


class SSLLetsEncryptTool:
    __re_pem = "(-+BEGIN (?:.+)-+[\\r\\n]+(?:[A-Za-z0-9+/=]{1,64}[\\r\\n]+)+-+END (?:.+)-+[\\r\\n]+)"
    __max_attempts = 3

    @classmethod
    def account(cls, email):
        config_model = ConfigDao()
        config = config_model.get_active()
        reg_file = f"{APP_BASE}/keystore/account_reg.json"
        key_file = f"{APP_BASE}/keystore/account_key.json"
        try:
            with open(reg_file, "r") as fr:
                registry = messages.RegistrationResource.json_loads(fr.read())
                with open(key_file, "r") as fk:
                    key = jose.JWK.json_loads(fk.read())
                    return {"key": key, "registry": registry}
        except Exception as ex:
            key = jose.JWKRSA(key=SSLTool.generate_private_key())
            net = client.ClientNetwork(key)
            directory = messages.Directory.from_json(
                net.get(config["acme_directory_url"]).json()
            )
            client_acme = client.ClientV2(directory, net=net)
            registry = client_acme.new_account(
                messages.NewRegistration.from_data(
                    email=email, terms_of_service_agreed=True
                )
            )
            with open(key_file, "w") as f:
                f.write(key.json_dumps())
            with open(reg_file, "w") as f:
                f.write(registry.json_dumps())

            return {"key": key, "registry": registry}

    @classmethod
    def create_certificate(cls, domain,sans=None, email="fake@tooka.com.br"):
        domain_list=[domain]
        if sans:
            domain_list.extend(sans)
        logger.info(f"Create certificate for {domain_list}")

        crt_key = SSLTool.generate_private_key()
        csr = SSLTool.gen_csr(domain_list, crt_key)

        config_model = ConfigDao()
        config = config_model.get_active()

        account = cls.account(email)

        net = client.ClientNetwork(key=account["key"], account=account["registry"])
        directory = messages.Directory.from_json(
            net.get(config["acme_directory_url"]).json()
        )
        acme = client.ClientV2(directory, net=net)

        order = acme.new_order(csr)
        for challenge in cls.challenge_body(order):
            token = challenge.path.rsplit("/", 1)[1]
            validation = challenge.validation(account["key"])
            response, validation = challenge.response_and_validation(acme.net.key)
            ch_model = ChallengeDao()
            ch_model.persist(
                {"key": token, "content": validation, "issued": datetime.now()}
            )
            acme.answer_challenge(challenge, response)

        for _ in range(cls.__max_attempts):
            try:
                finalized_order = acme.poll_and_finalize(order)
                chain_pem = re.findall(cls.__re_pem, finalized_order.fullchain_pem)
                chain = []
                for cp in chain_pem:
                    chain.append(SSLTool.crt_from_pem(cp))
                crt = chain.pop(0)

                certificate_dict = {
                    "chain": chain,
                    "certificate": crt,
                    "private_key": crt_key,
                }
                certificate_dict.update(SSLTool.extract_info_from_crt(crt))
                return certificate_dict
            except Exception as e:
                logger.error(f"{order} retry in 10 seconds")
                time.sleep(10)
        return None

    @classmethod
    def challenge_body(cls, new_order):
        authz_list = new_order.authorizations
        challenge = []

        for authz in authz_list:
            for i in authz.body.challenges:
                if isinstance(i.chall, challenges.HTTP01):
                    challenge += [i]
        return challenge
