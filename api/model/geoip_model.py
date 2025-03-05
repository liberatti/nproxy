from api.model.mongo_base_model import MongoDAO


class GeoIpDao(MongoDAO):
    def __init__(self):
        super().__init__("geoip")

    def find_by_ip(self, ip):
        query = {
            "$and": [
                {"range_start": {"$lte": ip}},
                {"range_end": {"$gte": ip}}
            ]
        }
        rs = self.collection.find_one(query)
        self._load(rs)
        return rs
