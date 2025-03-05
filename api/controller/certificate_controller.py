from datetime import datetime, timedelta

from flask import Blueprint, request
from marshmallow import ValidationError

from api.common_utils import ResponseBuilder, deep_merge, has_any_authority, get_pagination, replace_tz
from api.common_utils import socketio
from api.model.certificate_model import CertificateDao
from api.model.config_model import ChangeDao
from api.model.service_model import ServiceDao
from api.tools.ssl_tool import SSLTool
from config import TZ

routes = Blueprint("certificate", __name__)

@routes.before_request
def before():
    if request.method in ["PUT", "POST", "DELETE","PATCH"]:
        dao = ChangeDao()
        if not dao.get_by_name("certificate"):
            dao.persist({"name": "certificate"})
        socketio.emit('tracking_evt')


@routes.route("/<certificate_id>", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def get(certificate_id):
    dao = CertificateDao()
    certificate = dao.get_by_id(certificate_id)
    if certificate:
        return ResponseBuilder.data(certificate, schema=dao.schema)
    else:
        return ResponseBuilder.error_404()

@routes.route("", methods=["GET"])
@has_any_authority(["viewer", "superuser"])
def search():
    dao = CertificateDao()
    _filters = []
    result = dao.get_all(pagination=get_pagination(), filters=_filters)

    if result and result["metadata"]["total_elements"] > 0:
      renew_date = replace_tz(datetime.now())
      for c in result["data"]:
        if (c["force_renew"] or replace_tz(c["not_after"]) < renew_date):
          c.update({"status": "EXPIRED"})
        else:
          c.update({"status": "VALID"})
      return ResponseBuilder.data(result, schema=dao.pageSchema)
    else:
        return ResponseBuilder.error_404()

@routes.route("", methods=["POST"])
@has_any_authority(["superuser"])
def save():
    dao = CertificateDao()
    try:
        dto = dao.json_load(request.json)
        pk=None
        if 'EXTERNAL' in dto['provider']:
          crt = SSLTool.crt_from_pem(dto["certificate"])
          dto.update(SSLTool.extract_info_from_crt(crt))
          if dto["not_after"] <= datetime.now(TZ):
            dto.update({"status": "EXPIRED"})
          else:
            dto.update({"status": "VALID"})
          dto.update({'force_renew':False})
          pk = dao.persist(dto)

        if dto["provider"] in ["MANAGED", "SELF"]:
            self_crt = SSLTool.create_certificate("localhost")
            self_chain = []
            for c in self_crt["chain"]:
                self_chain.append(SSLTool.crt_to_pem(c))
            crt = {
                "name": dto["name"],
                "chain": "\n".join(self_chain),
                "certificate": SSLTool.crt_to_pem(self_crt["certificate"]),
                "private_key": SSLTool.private_to_pem(self_crt["private_key"]),
                "subjects": self_crt["subjects"],
                "not_before": self_crt["not_before"],
                "not_after": self_crt["not_after"],
                "force_renew": True,
                "provider":dto["provider"]
            }
            pk = dao.persist(crt)

        certificate = dao.get_by_id(pk)
        return ResponseBuilder.data(certificate, schema=dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)
    
@routes.route("/<certificate_id>", methods=["PUT"])
@has_any_authority(["superuser"])
def update(certificate_id):
    dao = CertificateDao()
    try:
        dto = dao.json_load(request.json)
        if dto['provider'] in ['EXTERNAL']:
          crt = SSLTool.crt_from_pem(dto["certificate"])
          dto.update(SSLTool.extract_info_from_crt(crt))
          if dto["not_after"] <= datetime.now(TZ):
            dto.update({"status": "EXPIRED"})
          else:
            dto.update({"status": "VALID"})
          dto.update({'force_renew':True})
          dao.update_by_id(certificate_id, dto)
          
        if dto["provider"] in ["MANAGED", "SELF"]:
            self_crt = SSLTool.create_certificate("localhost")
            self_chain = []
            for c in self_crt["chain"]:
                self_chain.append(SSLTool.crt_to_pem(c))
            crt = {
                "name": dto["name"],
                "chain": "\n".join(self_chain),
                "certificate": SSLTool.crt_to_pem(self_crt["certificate"]),
                "private_key": SSLTool.private_to_pem(self_crt["private_key"]),
                "subjects": self_crt["subjects"],
                "not_before": self_crt["not_before"],
                "not_after": self_crt["not_after"],
                "force_renew": True,
                "provider":dto["provider"]
            }
            dao.update_by_id(certificate_id, crt)
        
        return ResponseBuilder.data(dto, schema=dao.schema)
    except ValidationError as err:
        return ResponseBuilder.error_parse(err)

@routes.route("/<certificate_id>", methods=["PATCH"])
@has_any_authority(["superuser"])
def partial_update(certificate_id):
    dao = CertificateDao()
    try:
        c_new = dao.json_load(request.json)
        c_old = dao.get_by_id(certificate_id)

        dao.update_by_id(certificate_id,deep_merge(c_old,c_new))
        return ResponseBuilder.ok("Certificate partially updated")

    except ValidationError as err:
        return ResponseBuilder.error_parse(err)
    except Exception as err:
        return ResponseBuilder.error(msg=err)


@routes.route("/<certificate_id>", methods=["DELETE"])
@has_any_authority(["superuser"])
def delete(certificate_id):
    dao = CertificateDao()
    dao_service = ServiceDao()
    service_list = dao_service.get_all()
    in_use = False
    if "data" in service_list:
        for s in service_list["data"]:
            for b in s['bindings']:
              if b['protocol'] == 'HTTPS' and  certificate_id in b["certificate"]["_id"]:
                 in_use = True
                 break
    if in_use:
        return ResponseBuilder.error_500("Certificate in use")
    else:
        result = dao.delete_by_id(certificate_id)
        if result:
            return ResponseBuilder.data_removed(certificate_id)
        else:
            return ResponseBuilder.error_404()
