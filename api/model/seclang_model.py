from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from marshmallow import EXCLUDE, Schema, fields

from common_utils import logger
from model.mongo_base_model import MongoDAO


class DataObjectSchema(Schema):
    """
    Schema for data object validation and serialization.
    
    This schema defines the structure and validation rules for data objects.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String()
    content = fields.List(fields.String())


class SecBaseSchema(Schema):
    """
    Base schema for security language validation and serialization.
    
    This schema defines the common structure and validation rules
    for security language documents.
    """
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
    def schema_class(cls, schema_type: str) -> type:
        """
        Returns the appropriate schema class based on the schema type.
        
        Args:
            schema_type (str): Type of schema to return
            
        Returns:
            type: Schema class
            
        Raises:
            ValueError: If the schema type is unknown
        """
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
    """
    Schema for security action validation and serialization.
    
    This schema defines the structure and validation rules for security actions.
    """
    class Meta:
        unknown = EXCLUDE

    initcol = fields.List(fields.String())
    t = fields.List(fields.String())
    setvar = fields.List(fields.String())
    tag = fields.String()


class SecComponentSignature(SecBaseSchema):
    """
    Schema for component signature validation and serialization.
    
    This schema defines the structure and validation rules for component signatures.
    """
    class Meta:
        unknown = EXCLUDE

    text = fields.String()


class SecMarker(SecBaseSchema):
    """
    Schema for security marker validation and serialization.
    
    This schema defines the structure and validation rules for security markers.
    """
    class Meta:
        unknown = EXCLUDE

    text = fields.String()


class SecRule(SecBaseSchema):
    """
    Schema for security rule validation and serialization.
    
    This schema defines the structure and validation rules for security rules.
    """
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
    chain_starter = fields.Boolean(allow_none=False, load_default=False, dump_default=False)
    chain = fields.Nested("SecRule", many=True, allow_none=True)


class RuleCategorySchema(Schema):
    """
    Schema for rule category validation and serialization.
    
    This schema defines the structure and validation rules for rule categories.
    """
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    name = fields.String(required=True)
    phase = fields.Integer(required=True)
    file = fields.String(required=False)
    rules = fields.Nested(SecBaseSchema, many=True)
    exclusions = fields.List(fields.Integer(), allow_none=True)


class RuleDao(MongoDAO):
    """
    DAO for managing security rules.
    
    This class extends MongoDAO to provide specific operations
    related to security rule management.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'rules' collection and schema.
        """
        super().__init__("rules", schema=SecRule)

    def get_by_code(self, code: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a rule by its code.
        
        Args:
            code (int): Rule code
            
        Returns:
            Optional[Dict[str, Any]]: Rule document or None if not found
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"code": int(code)}
            logger.debug(query)
            vo = self.collection.find_one(query)
            self._to_dict(vo)
            return vo
        except Exception as e:
            logger.error(f"Error retrieving rule by code: {str(e)}")
            raise

    def find_all_by_category_id(self, category_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all rules for a specific category.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            List[Dict[str, Any]]: List of rule documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {{"category_id": {"$eq": category_id}}, {"$sort": {"rule_order": 1}}}
            logger.debug(query)
            rows = self.collection.find(query)
            for r in rows:
                 self._to_dict(r)
            return rows
        except Exception as e:
            logger.error(f"Error finding rules by category: {str(e)}")
            raise

    def _to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Loads a rule document with its category information.
        
        Args:
            vo (Optional[Dict[str, Any]]): Rule document to load
            
        Returns:
            Optional[Dict[str, Any]]: Loaded rule document
        """
        if vo:
            super()._to_dict(vo)
            daoc = RuleCategoryDao()
            vo.update({"category": daoc.get_descr_by_id(vo.pop("category_id"))})
        return vo


class RuleCategoryDao(MongoDAO):
    """
    DAO for managing rule categories.
    
    This class extends MongoDAO to provide specific operations
    related to rule category management.
    """
    
    def __init__(self):
        """
        Initializes the DAO with the 'rule_cat' collection and schema.
        """
        super().__init__("rule_cat", schema=RuleCategorySchema)


    def get_all(self, pagination: Optional[Dict[str, Any]] = None, 
                dt_start: Optional[datetime] = None, 
                dt_end: Optional[datetime] = None, 
                filters: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Retrieves all rule categories with optional filtering and pagination.
        
        Args:
            pagination (Optional[Dict[str, Any]]): Pagination parameters
            dt_start (Optional[datetime]): Start date filter
            dt_end (Optional[datetime]): End date filter
            filters (Optional[List[Dict[str, Any]]]): Additional filters
            
        Returns:
            Dict[str, Any]: Dictionary with metadata and data
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = [
                {"$sort": {"phase": 1}},
            ]
            if pagination:
                query.append(
                    {
                        "$facet": {
                            "data": [
                                {
                                    "$skip": (
                                        (pagination["page"] - 1) * pagination["per_page"]
                                    )
                                },
                                {"$limit": pagination["per_page"]},
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
        except Exception as e:
            logger.error(f"Error retrieving rule categories: {str(e)}")
            raise

    def persist(self, vo: Dict[str, Any]) -> str:
        """
        Persists a rule category with its associated rules.
        
        Args:
            vo (Dict[str, Any]): Category data dictionary
            
        Returns:
            str: ID of the inserted category
            
        Raises:
            PyMongoError: If an error occurs during the insert operation
        """
        try:
            rules = vo.pop("rules")
            pk = super().persist(vo)
            rule_dao = RuleDao()
            rule_ids = []
            for r in rules:
                r.update({"category_id": ObjectId(pk)})
                rpk = rule_dao.persist(r)
                rule_ids.append(ObjectId(rpk))
            super().update_by_id(pk, {"rule_ids": rule_ids})
            return pk
        except Exception as e:
            logger.error(f"Error persisting rule category: {str(e)}")
            raise

    def get_by_phases(self, phases: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieves rule categories by their phases.
        
        Args:
            phases (List[int]): List of phases to search for
            
        Returns:
            List[Dict[str, Any]]: List of category documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            query = {"phase": {"$in": phases}}
            logger.debug(query)
            rows = list(self.collection.find(query))
            for vo in rows:
                if vo:
                    vo.update({"_id": str(vo["_id"])})
            return rows
        except Exception as e:
            logger.error(f"Error retrieving categories by phases: {str(e)}")
            raise

    def get_by_name_and_phases(self, name: str, phases: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieves rule categories by name and phases.
        
        Args:
            name (str): Category name to search for
            phases (List[int]): List of phases to search for
            
        Returns:
            List[Dict[str, Any]]: List of category documents
            
        Raises:
            PyMongoError: If an error occurs during the search operation
        """
        try:
            rows = self.collection.find(
                {"name": {"$regex": f".*{name}.*"}}, {"phase": {"$eq": phases}}
            )
            return rows
        except Exception as e:
            logger.error(f"Error retrieving categories by name and phases: {str(e)}")
            raise

    def _to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Loads a category document with its associated rules.
        
        Args:
            vo (Optional[Dict[str, Any]]): Category document to load
            
        Returns:
            Optional[Dict[str, Any]]: Loaded category document
        """
        super()._to_dict(vo)
        if vo and "rule_ids" in vo:
            rules = []
            dao_rule = RuleDao()
            for r_id in vo.pop("rule_ids"):
                rules.append(dao_rule.get_by_id(r_id))
            vo.update({"rules": rules})
        return vo
