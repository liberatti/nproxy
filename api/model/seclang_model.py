from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from api.common_utils import logger
from api.model.dictionary_model import DataObjectSchema
from api.model.mongo_base_model import MongoDAO


class SecBaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String(allow_none=True)
    schema_type = fields.String()
    code = fields.Integer()
    rule_order = fields.Integer(allow_none=True)
    phase = fields.Integer()
    action = fields.String()
    logging = fields.String()
    audit_log = fields.String()
    version = fields.String()

    @classmethod
    def schema_class(cls, schema_type):
        schema_classes = {
            "SecAction": SecAction,
            "SecMarker": SecMarker,
            "SecRule": SecRule,
            "SecComponentSignature": SecComponentSignature,
        }

        if schema_type in schema_classes:
            return schema_classes[schema_type]
        else:
            raise ValueError(f"Unknown type: {schema_type}")


class SecAction(SecBaseSchema):
    class Meta:
        unknown = EXCLUDE

    initcol = fields.List(fields.String())
    t = fields.List(fields.String())
    setvar = fields.List(fields.String())
    tag = fields.String()


class SecComponentSignature(SecBaseSchema):
    class Meta:
        unknown = EXCLUDE

    text = fields.String()


class SecMarker(SecBaseSchema):
    class Meta:
        unknown = EXCLUDE

    text = fields.String()


class SecRule(SecBaseSchema):
    class Meta:
        unknown = EXCLUDE

    msg = fields.String(allow_none=True)
    comment = fields.String(allow_none=True)
    skip_after = fields.String(allow_none=True)
    logdata = fields.String(allow_none=True)
    severity = fields.String(allow_none=True)
    condition = fields.String(allow_none=True)
    t = fields.List(fields.String(), allow_none=True)
    ctl = fields.List(fields.String(), allow_none=True)
    scope = fields.List(fields.String(), allow_none=True)
    tags = fields.List(fields.String(), allow_none=True)
    setvar = fields.List(fields.String(), allow_none=True)
    expirevar = fields.List(fields.String(), allow_none=True)
    capture = fields.Boolean(allow_none=True)
    multi_match = fields.Boolean(allow_none=True)
    status = fields.Integer(allow_none=True)
    files = fields.List(fields.Nested(DataObjectSchema), allow_none=True)
    chain_starter = fields.Boolean(allow_none=False, default=False)
    chain = fields.Nested("SecRule", many=True, allow_none=True)


class RuleCategorySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String(required=True)
    phase = fields.Integer(required=True)
    file = fields.String(required=False)
    rules = fields.Nested(SecBaseSchema, many=True)
    exclusions = fields.List(fields.Integer(), allow_none=True)


class RuleDao(MongoDAO):
    def __init__(self):
        super().__init__("rules", schema=SecRule)

    def get_by_code(self, code):
        query = {"code": int(code)}
        logger.debug(query)
        vo = self.collection.find_one(query)
        self._load(vo)
        return vo

    def find_all_by_category_id(self, category_id):
        query = {{"category_id": {"$eq": category_id}}, {"$sort": {"rule_order": 1}}}
        logger.debug(query)
        rows = self.collection.find(query)
        for r in rows:
            self._load(r)
        return rows

    def _load(self, vo):
        if vo:
            super()._load(vo)
            daoc = RuleCategoryDao()
            vo.update({"category": daoc.get_descr_by_id(vo.pop('category_id'))})


class RuleCategoryDao(MongoDAO):
    def __init__(self):
        super().__init__("rule_cat", schema=RuleCategorySchema)

    def get_all(
            self, pagination=None, dt_start=None, dt_end=None, filters=None
    ):
        query = [
            {"$sort": {"phase": 1}},
        ]
        if pagination:
            query.append(
                {
                    "$facet": {
                        "data": [
                            {"$skip": ((pagination['page'] - 1) * pagination['per_page'])},
                            {"$limit": pagination['per_page']},
                        ],
                        "pagination": [{"$count": "total"}],
                    }
                }
            )
        else:
            query.append({"$facet": {"data": []}})
        if filters:
            for f in filters:
                query[0]["$match"].update(f)

        logger.debug(query)
        rs = list(self.collection.aggregate(query))[0]
        return self._fetch_all(rs, pagination=pagination)

    def persist(self, vo):
        rules = vo.pop("rules")
        pk = super().persist(vo)
        rule_dao = RuleDao()
        rule_ids = []
        for r in rules:
            r.update({"category_id": ObjectId(pk)})
            rpk = rule_dao.persist(r)
            rule_ids.append(ObjectId(rpk))
        super().update_by_id(pk, {"rule_ids": rule_ids})

    def get_by_phases(self, phases):
        query = {"phase": {"$in": phases}}
        logger.debug(query)
        rows = list(self.collection.find(query))
        for vo in rows:
            if vo:
                vo.update({"_id": str(vo["_id"])})
        return rows

    def get_by_name_and_phases(self, name, phases):
        rows = self.collection.find(
            {"name": {"$regex": f".*{name}.*"}}, {"phase": {"$eq": phases}}
        )
        return rows

    def _load(self, vo):
        super()._load(vo)
        if vo and "rule_ids" in vo:
            rules = []
            dao_rule = RuleDao()
            for r_id in vo.pop("rule_ids"):
                rules.append(dao_rule.get_by_id(r_id))
            vo.update({"rules": rules})
        return vo
