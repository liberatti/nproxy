from api.model.mongo_base_model import MongoDAO


class ChallengeDao(MongoDAO):
    def __init__(self):
        super().__init__("challenge")

    def delete_issued_before(self, dt):
        self.collection.delete_many({"issued": {"$lt": dt}})

    def get_by_key(self, key):
        rs = self.collection.find_one({"key": key})
        self._load(rs)
        return rs
