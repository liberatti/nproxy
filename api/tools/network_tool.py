import ipaddress
import socket
from typing import Dict, List, Optional, Tuple, Union

from common_utils import logger


class NetworkTool:
    """Network utility class for handling IP addresses and network operations.
    
    This class provides methods for:
    - IP address resolution and validation
    - Network address manipulation
    - IP address format conversion
    - Network range calculations
    """
    
    @classmethod
    def hostbyname(cls, ns: str) -> Optional[str]:
        """Resolve a hostname to its IP address.
        
        Args:
            ns: Hostname to resolve
            
        Returns:
            IP address as string if resolution successful, None otherwise
        """
        try:
            return socket.gethostbyname(ns)
        except socket.gaierror as e:
            logger.error(f"Name resolution failed for '{ns}': {e}")
            return None

    @classmethod
    def id(cls, ip: str) -> str:
        """Convert an IP address to its expanded form.
        
        Args:
            ip: IP address to expand
            
        Returns:
            Expanded IP address as string
        """
        return cls.expand_ip(ip)

    @classmethod
    def is_host(cls, ip: str) -> bool:
        """Check if a string is a valid IP address.
        
        Args:
            ip: String to validate as IP address
            
        Returns:
            True if valid IP address, False otherwise
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except Exception:
            return False

    @classmethod
    def is_network(cls, net: str) -> bool:
        """Check if a string is a valid network address.
        
        Args:
            net: String to validate as network address
            
        Returns:
            True if valid network address, False otherwise
        """
        try:
            ipaddress.ip_network(net, strict=False)
            return True
        except ipaddress.NetmaskValueError:
            return False
        except ValueError:
            return False

    @classmethod
    def aggregate(cls, addr_list: List[str]) -> List[str]:
        """Aggregate a list of IP addresses/networks into the most efficient network ranges.
        
        Args:
            addr_list: List of IP addresses or networks to aggregate
            
        Returns:
            List of aggregated network ranges
        """
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
    def hosts_from_net(cls, masked_ip: str) -> List[str]:
        """Get all host IP addresses from a network.
        
        Args:
            masked_ip: Network address in CIDR notation
            
        Returns:
            List of host IP addresses in the network
        """
        try:
            network = ipaddress.IPv4Network(masked_ip, strict=False)
            return [str(ip) for ip in network.hosts()]
        except Exception as e:
            logger.error(f"Failed to get hosts from network {masked_ip}: {e}")
            return []

    @classmethod
    def is_ipv4(cls, ip: str) -> bool:
        """Check if an IP address is IPv4.
        
        Args:
            ip: IP address to check
            
        Returns:
            True if IPv4 address, False otherwise
        """
        try:
            return ipaddress.ip_network(ip, strict=False).version == 4
        except Exception:
            return False

    @classmethod
    def expand_ip(cls, ip):
        """Expand an IP address to its full form.
        
        For IPv4 addresses, pads each octet with leading zeros.
        For IPv6 addresses, expands to full form.
        
        Args:
            ip: IP address to expand
            
        Returns:
            Expanded IP address as string
        """
        if cls.is_ipv4(ip):
            parts = ip.split(".")
            parts_with_zero = [part.zfill(3) for part in parts]
            return ".".join(parts_with_zero)
        return str(ipaddress.ip_address(ip).exploded)

    @classmethod
    def masklen_from_network(cls, addr: str, netmask: str) -> int:
        """Calculate network mask length from address and netmask.
        
        Args:
            addr: Network address
            netmask: Network mask
            
        Returns:
            Mask length as integer
        """
        return ipaddress.ip_network(f"{addr}/{netmask}", strict=False).prefixlen

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
