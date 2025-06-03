import {Injectable, Injector} from '@angular/core';
import {HttpParams} from '@angular/common/http';
import {Observable} from 'rxjs';
import {PageMeta} from '../models/shared';
import {TransactionFilter, TransactionLog} from '../models/transaction';
import {APIService} from './api.service';
import {LocalStorageService} from './localstorage.service';
import moment from 'moment';
import {API_DATA_FORMAT} from "../app.config";

@Injectable({
    providedIn: 'root'
})
export class TransactionService extends APIService<TransactionLog, number> {
    private config;
    protected _API_DATA_FORMAT :string;
    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService,
    ) {
        super(injector, 'trn')
        this._API_DATA_FORMAT = injector.get(API_DATA_FORMAT)
        this.config = this.localStorage.get("ui_config");
    }

    getTpm(filter: TransactionFilter): Observable<any> {
        let t_list = []
        if (filter.filters)
            for (let i = 0; i < filter.filters.length; i++) {
                t_list.push(JSON.parse(filter.filters[i]))
            }
        /*
              const f = {
            "logtime_start": moment(filter.start).subtract(1, 'day').startOf('day').format(this._API_DATA_FORMAT),
            'logtime_end': moment(filter.end).endOf('day').format(this._API_DATA_FORMAT),
            'filters': t_list
        };
        * */
        const f = {
            "logtime_start": moment(filter.start).utc().format(this._API_DATA_FORMAT),
            'logtime_end': moment(filter.end).utc().format(this._API_DATA_FORMAT),
            'filters': t_list
        };
        return this.httpClient.post<any>(this.END_POINT + '/stats/tpm', f);
    }

    search(filter: TransactionFilter, pagination?: PageMeta): Observable<any> {
        let f_list = []
        if (filter.filters)
            for (let i = 0; i < filter.filters.length; i++) {
                f_list.push(JSON.parse(filter.filters[i]))
            }
        const f = {
            "logtime_start": moment(filter.start).utc().format(this._API_DATA_FORMAT),
            'logtime_end': moment(filter.end).utc().format(this._API_DATA_FORMAT),
            'filters': f_list
        };
        let options = {
            params: new HttpParams()
        }
        if (pagination) {
            options.params = options.params.append("page", pagination.page);
            options.params = options.params.append("size", pagination.per_page);
        }
        return this.httpClient.post<any>(this.END_POINT, f, options);
    }
}