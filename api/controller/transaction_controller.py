from datetime import datetime

from flask import Blueprint, request

from common_utils import ResponseBuilder, has_any_authority, get_pagination, replace_tz
from model.transaction_model import TransactionDao
from config import DATETIME_FMT

routes = Blueprint("trn", __name__)


@routes.route("/stats/tpm", methods=["POST"])
@has_any_authority(authorities=["viewer", "superuser"])
def st_tpm():
    req = request.json
    st_date = replace_tz(datetime.strptime(req.pop("logtime_start"), DATETIME_FMT))
    ed_date = replace_tz(datetime.strptime(req.pop("logtime_end"), DATETIME_FMT))
    dao = TransactionDao()
    if "filters" in req:
        tpm = dao.get_tpm(
            st_date,
            ed_date,
            req["filters"],
        )
    else:
        tpm = dao.get_tpm(
            st_date,
            ed_date,
            None,
        )
    if tpm:
        for s in tpm:
            dtj = s.pop("_id")
            dt = replace_tz(datetime(
                dtj["year"], dtj["month"], dtj["day"], dtj["hour"], dtj["minute"]
            ))
            s.update({"logtime": dt.strftime(DATETIME_FMT)})
        return ResponseBuilder.data(tpm)
    else:
        return ResponseBuilder.error_404()


@routes.route("/<trn_id>", methods=["GET"])
@has_any_authority(authorities=["viewer", "superuser"])
def get(trn_id):
    dao = TransactionDao()
    trn = dao.get_by_id(trn_id)

    if trn:
        return ResponseBuilder.data(trn, dao.schema)
    else:
        return ResponseBuilder.error_404()


@routes.route("", methods=["POST"])
@has_any_authority(authorities=["viewer", "superuser"])
def search():
    dao = TransactionDao()
    st_date = replace_tz(datetime.strptime(
        request.json.pop("logtime_start"), DATETIME_FMT
    ))
    ed_date = replace_tz(datetime.strptime(request.json.pop("logtime_end"), DATETIME_FMT))
    _pagination = get_pagination()
    if request.json and "filters" in request.json:
        result = dao.get_all(
            _pagination,
            dt_start=st_date,
            dt_end=ed_date,
            filters=request.json["filters"],
        )
    else:
        result = dao.get_all(
            _pagination,
            dt_start=st_date,
            dt_end=ed_date,
            filters=None,
        )
    if result["metadata"]["total_elements"] > 0:
        return ResponseBuilder.data(result, dao.pageSchema)
    else:
        return ResponseBuilder.error_404()
