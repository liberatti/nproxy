from datetime import datetime, timedelta

from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import replace_tz
from api.model.mongo_base_model import MongoDAO
from config import DATETIME_FMT


class CertificateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    subjects = fields.List(fields.String())
    chain = fields.String()
    certificate = fields.String()
    private_key = fields.String()
    ssl_client_ca = fields.String()
    not_before = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)
    not_after = fields.DateTime(format=DATETIME_FMT, allow_none=True, required=False)
    status = fields.String(required=False)
    provider = fields.String(required=False)
    force_renew = fields.Boolean(required=False, default=False)


class CertificateDao(MongoDAO):
    def __init__(self):
        super().__init__("certificate", schema=CertificateSchema)

    def count_by_status(self):
        query = [
            {"$facet": {"data": [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]}}
        ]
        rs = list(self.collection.aggregate(query))[0]
        rows = rs.get("data", [])
        return {rows[0]["_id"]: rows[0]["count"], rows[1]["_id"]: rows[1]["count"]}

    def persist(self, o):
        default_date = (
            replace_tz((datetime.now() - timedelta(days=1)))
            .replace(microsecond=0)
        )
        if "not_after" not in o:
            o.update({"not_after": default_date})

        if "not_before" not in o:
            o.update({"not_before": default_date})
        return super().persist(o)
