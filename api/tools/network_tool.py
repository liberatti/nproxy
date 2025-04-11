import ipaddress
import socket

from api.common_utils import logger


class NetworkTool:
    @classmethod
    def hostbyname(cls, ns):
        try:
            return socket.gethostbyname(ns)
        except socket.gaierror as e:
            logger.error(f"Name resolution failed for '{ns}': {e}")
            return None

    @classmethod
    def id(cls, ip):
        return cls.expand_ip(ip)

    @classmethod
    def is_host(cls, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except Exception:
            return False

    @classmethod
    def is_network(cls, net):
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
        nets = sorted(nets, key=lambda n1: n1.prefixlen)
        uq_nets = []
        while nets:
            n = nets.pop(0)
            if not any(n.subnet_of(un) for un in uq_nets):
                uq_nets.append(n)
        return [str(r) for r in uq_nets]

    @classmethod
    def hosts_from_net(cls, masked_ip):
        network = ipaddress.IPv4Network(masked_ip, strict=False)
        return [str(ip) for ip in network.hosts()]

    @classmethod
    def is_ipv4(cls, ip):
        try:
            if cls.is_network(ip):
                network = ipaddress.ip_network(ip, strict=False)
                addr_ini = network.network_address
            else:
                addr_ini = ipaddress.ip_address(cls.compress_ip(ip))
            return addr_ini.version == 4
        except ValueError as e:
            logger.info(e)
            return False

    @classmethod
    def expand_ip(cls, ip):
        if cls.is_ipv4(ip):
            parts = ip.split(".")
            parts_with_zero = [part.zfill(3) for part in parts]
            return ".".join(parts_with_zero)
        return str(ipaddress.ip_address(ip).exploded)

    @classmethod
    def compress_ip(cls, ip):
        return str(ipaddress.ip_address(ip).compressed)

    @classmethod
    def masklen_from_network(cls, addr, netmask):
        net = ipaddress.ip_network(f"{addr}/{netmask}", strict=False)
        return net.prefixlen

    @classmethod
    def range_from_network(cls, net):
        v = 6
        if cls.is_ipv4(net):
            v = 4
            rede = ipaddress.IPv4Network(net, strict=False)
        else:
            rede = ipaddress.IPv6Network(net, strict=False)
        return {
            "net_start": cls.id(str(rede.network_address)),
            "net_end": cls.id(str(rede.broadcast_address)),
            "version": v,
        }

    @classmethod
    def calc_prefix_from_range(cls, ip_ini, ip_end):
        addr_ini = ipaddress.ip_address(ip_ini)
        addr_end = ipaddress.ip_address(ip_end)
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
