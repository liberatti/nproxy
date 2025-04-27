import unittest
from ipaddress import IPv4Address, IPv6Address

from tools.network_tool import NetworkTool


class TestNetworkTool(unittest.TestCase):
    def setUp(self):
        self.ipv4_public = "8.8.8.8"
        self.ipv4_private = "192.168.1.1"
        self.ipv4_loopback = "127.0.0.1"
        self.ipv4_multicast = "224.0.0.1"
        self.ipv6_public = "2001:4860:4860::8888"
        self.ipv6_private = "fc00::1"
        self.ipv6_loopback = "::1"
        self.ipv6_multicast = "ff02::1"
        self.invalid_ip = "invalid.ip.address"

    def test_hostbyname(self):
        self.assertIsNotNone(NetworkTool.hostbyname("google.com"))

    def test_is_host(self):
        self.assertTrue(NetworkTool.is_host(self.ipv4_public))
        self.assertTrue(NetworkTool.is_host(self.ipv6_public))
        self.assertFalse(NetworkTool.is_host(self.invalid_ip))

    def test_is_network(self):
        self.assertTrue(NetworkTool.is_network("192.168.1.0/24"))
        self.assertTrue(NetworkTool.is_network("2001:db8::/32"))
        self.assertFalse(NetworkTool.is_network(self.invalid_ip))

    def test_is_ipv4(self):
        self.assertTrue(NetworkTool.is_ipv4(self.ipv4_public))
        self.assertFalse(NetworkTool.is_ipv4(self.ipv6_public))
        self.assertFalse(NetworkTool.is_ipv4(self.invalid_ip))


    def test_expand_ip(self):
        self.assertEqual(NetworkTool.expand_ip("192.168.1.1"), "192.168.001.001")
        self.assertEqual(
            NetworkTool.expand_ip("2001:db8::1"),
            "2001:0db8:0000:0000:0000:0000:0000:0001",
        )
        
    def test_range_from_network(self):
        result = NetworkTool.range_from_network("192.168.1.0/24")
        self.assertEqual(result["net_start"], "192.168.001.000")
        self.assertEqual(result["net_end"], "192.168.001.255")
        self.assertEqual(result["version"], 4)

    def test_calc_prefix_from_range(self):
        self.assertEqual(
            NetworkTool.calc_prefix_from_range("192.168.1.1", "192.168.1.254"), 24
        )
        with self.assertRaises(ValueError):
            NetworkTool.calc_prefix_from_range("192.168.1.254", "192.168.1.1")
