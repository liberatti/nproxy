from api.model.mongo_base_model import MongoDAO
from api.tools.network_tool import NetworkTool


class GeoIpDao(MongoDAO):
    def __init__(self):
        super().__init__("geoip")

    def find_by_ip(self, ip):
        ip_id = NetworkTool.id(ip)
        query = {"$and": [{"net_start": {"$lte": ip_id}}, {"net_end": {"$gte": ip_id}}]}
        rs = self.collection.find_one(query)
        self._load(rs)
        return rs
