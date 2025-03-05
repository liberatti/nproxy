from marshmallow import EXCLUDE, Schema, fields

from api.model.mongo_base_model import MongoDAO


class ConfigArchiveSchema(Schema):
    enabled = fields.Boolean()
    archive_after = fields.Integer()  # minutes
    purge_after = fields.Integer()  # days
    type = fields.String()  # elastic_search, opensearch, syslog
    url = fields.String()
    username = fields.String()
    password = fields.String()


class ConfigPurgeSchema(Schema):
    enabled = fields.Boolean()
    purge_after = fields.Integer()  # days


class ConfigSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    maxmind_key = fields.String()
    ca_certificate = fields.String()
    ca_private = fields.String()
    acme_directory_url = fields.String()
    archive = fields.Nested(ConfigArchiveSchema)
    purge = fields.Nested(ConfigPurgeSchema)


class ConfigDao(MongoDAO):
    def __init__(self):
        super().__init__("config", schema=ConfigSchema)

    def get_active(self):
        rs = self.collection.find_one({})
        self._load(rs)
        return rs


class ChangeDao(MongoDAO):
    def __init__(self):
        super().__init__("changes")
