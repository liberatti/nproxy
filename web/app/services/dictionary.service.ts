import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Dictionary} from "../models/dictionary";
import {LocalStorageService} from "./localstorage.service";
import {Page, PageMeta} from "../models/shared";
import {Observable} from "rxjs";
import {HttpParams} from "@angular/common/http";

@Injectable({
    providedIn: 'root'
})
export class DictionaryService extends APIService<Dictionary, string> {

    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService
    ) {
        super(injector, 'dictionary')
    }

    search(filter: any, pagination?: PageMeta): Observable<Page> {
        let opts = {
            params: new HttpParams()
        }
        opts.params = opts.params.append("user_only", filter.userOnly);
        opts.params = opts.params.append("regex", filter.regex);
        if (pagination) {
            opts.params = opts.params.append("page", pagination.page);
            opts.params = opts.params.append("size", pagination.per_page);
        }
        return this.httpClient.get<Page>(this.END_POINT, opts);
    }
}