import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import josepy as jose
from acme import challenges, client, crypto_util, messages
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509.oid import NameOID

from tools.cluster_tool import ClusterTool
from common_utils import logger, replace_tz
from model.acme_model import ChallengeDao
from model.config_model import ConfigDao
from config import APP_BASE, KEY_SIZE, TZ


class SSLTool:
    """SSL/TLS certificate management utility class.
    
    This class provides methods for:
    - Private key generation and management
    - Certificate signing request (CSR) generation
    - Certificate authority (CA) operations
    - Certificate creation and management
    - Certificate information extraction
    """
    
    @classmethod
    def private_from_pem(cls, pem: str, password: Optional[str] = None) -> rsa.RSAPrivateKey:
        """Load a private key from PEM format.
        
        Args:
            pem: Private key in PEM format
            password: Optional password for encrypted private key
            
        Returns:
            RSAPrivateKey object
        """
        return serialization.load_pem_private_key(pem.encode(), password=password)

    @classmethod
    def private_to_pem(cls, pk: rsa.RSAPrivateKey) -> str:
        """Convert a private key to PEM format.
        
        Args:
            pk: RSAPrivateKey object
            
        Returns:
            Private key in PEM format as string
        """
        return pk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")

    @classmethod
    def crt_to_pem(cls, crt: x509.Certificate) -> str:
        """Convert a certificate to PEM format.
        
        Args:
            crt: Certificate object
            
        Returns:
            Certificate in PEM format as string
        """
        return crt.public_bytes(encoding=serialization.Encoding.PEM).decode("ascii")

    @classmethod
    def crt_from_pem(cls, pem: str) -> x509.Certificate:
        """Load a certificate from PEM format.
        
        Args:
            pem: Certificate in PEM format
            
        Returns:
            Certificate object
        """
        return x509.load_pem_x509_certificate(pem.encode(), default_backend())

    @classmethod
    def generate_private_key(cls) -> rsa.RSAPrivateKey:
        """Generate a new RSA private key.
        
        Returns:
            RSAPrivateKey object
        """
        return rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)

    @classmethod
    def gen_csr(cls, domain_names: List[str], pk: rsa.RSAPrivateKey) -> bytes:
        """Generate a certificate signing request (CSR).
        
        Args:
            domain_names: List of domain names to include in the CSR
            pk: Private key to use for signing the CSR
            
        Returns:
            CSR in DER format
        """
        pk_bytes = pk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return crypto_util.make_csr(pk_bytes, domain_names)

    @classmethod
    def gen_ca(cls, crt_cn: str, crt_org: Optional[str] = "Nproxy-CA") -> Dict[str, Union[x509.Certificate, rsa.RSAPrivateKey]]:
        """Generate a self-signed certificate authority (CA).
        
        Args:
            crt_cn: Common name for the CA certificate
            crt_org: Optional organization name for the CA certificate
            
        Returns:
            Dictionary containing the CA certificate and private key
        """
        ca_key = cls.generate_private_key()
        curr_date = datetime.now().astimezone(TZ)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Sao Paulo"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Sao Paulo"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, crt_org),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Internal"),
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
    def create_certificate(
        cls, 
        domain: str, 
        sans: Optional[List[str]] = None, 
        ca: Optional[Dict[str, Union[x509.Certificate, rsa.RSAPrivateKey]]] = None
    ) -> Dict:
        """Create a new SSL/TLS certificate.
        
        Args:
            domain: Main domain name for the certificate
            sans: Optional list of subject alternative names
            ca: Optional CA certificate and key to use for signing
            
        Returns:
            Dictionary containing the certificate, chain, private key and metadata
        """
        if not ca:
            ca = {
                "certificate": SSLTool.crt_from_pem(ClusterTool.CONFIG['config']['ca_certificate']),
                "private_key": SSLTool.private_from_pem(ClusterTool.CONFIG['config']['ca_private']),
            }

        curr_date = datetime.now().astimezone(TZ)
        server_key = cls.generate_private_key()

        if sans:
            san_list = [x509.DNSName(c) for c in list(set(sans))]
        else:
            san_list = []

        logger.info(f"Create certificate for {domain} with {sans}")

        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Sao Paulo"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Sao Paulo"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Nproxy-CA"),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Internal"),
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
    def extract_info_from_crt(cls, crt: x509.Certificate) -> Dict:
        """Extract information from a certificate.
        
        Args:
            crt: Certificate to extract information from
            
        Returns:
            Dictionary containing certificate subjects, validity dates
        """
        if not crt:
            raise ValueError("Certificate object is None or invalid")
        
        subjects = []
        for c in crt.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME):
            subjects.append(c.value)
        
        try:
            san_extension = crt.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            for c in san_extension.value:
                subjects.append(c.value)
        except x509.extensions.ExtensionNotFound:
            pass

        return {
            "subjects": list(OrderedDict.fromkeys(subjects)),
            "not_before": replace_tz(crt.not_valid_before).replace(microsecond=0),
            "not_after": replace_tz(crt.not_valid_after).replace(microsecond=0),
        }


class SSLLetsEncryptTool:
    """Let's Encrypt certificate management utility class.
    
    This class provides methods for:
    - Let's Encrypt account management
    - Automated certificate issuance
    - HTTP-01 challenge handling
    """
    
    __re_pem = "(-+BEGIN (?:.+)-+[\\r\\n]+(?:[A-Za-z0-9+/=]{1,64}[\\r\\n]+)+-+END (?:.+)-+[\\r\\n]+)"
    __max_attempts = 3

    @classmethod
    def account(cls, email: str) -> Dict:
        """Get or create a Let's Encrypt account.
        
        Args:
            email: Email address for the account
            
        Returns:
            Dictionary containing account key and registration
        """
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
        except Exception:
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
    def create_certificate(
        cls, 
        domain: str, 
        sans: Optional[List[str]] = None, 
        email: str = "fake@tooka.com.br"
    ) -> Optional[Dict]:
        """Create a new Let's Encrypt certificate.
        
        Args:
            domain: Main domain name for the certificate
            sans: Optional list of subject alternative names
            email: Email address for the Let's Encrypt account
            
        Returns:
            Dictionary containing the certificate, chain, private key and metadata,
            or None if certificate creation failed
        """
        domain_list = [domain]
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
            challenge.validation(account["key"])
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
            except Exception:
                logger.error(f"Order status: {order.body.status} - retry in 10 seconds")
                time.sleep(10)
        return None

    @classmethod
    def challenge_body(cls, new_order: messages.OrderResource) -> List[challenges.HTTP01]:
        """Extract HTTP-01 challenges from a new order.
        
        Args:
            new_order: Let's Encrypt order resource
            
        Returns:
            List of HTTP-01 challenges
        """
        authz_list = new_order.authorizations
        challenge = []

        for authz in authz_list:
            for i in authz.body.challenges:
                if isinstance(i.chall, challenges.HTTP01):
                    challenge += [i]
        return challenge
