import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Certificate} from "../models/certificate";
import {LocalStorageService} from "./localstorage.service";
import {Page, PageMeta} from "../models/shared";
import {Observable} from "rxjs";
import {HttpParams} from "@angular/common/http";

@Injectable({
    providedIn: 'root'
})
export class CertificateService extends APIService<Certificate, string> {

    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService
    ) {
        super(injector, 'certificate')
    }

    get_all_by_provider(provider: string, pagination?: PageMeta): Observable<Page> {
        const options = {
            params: new HttpParams()
        }
        options.params = options.params.append("provider", provider);
        if (pagination) {
            options.params = options.params.append("page", pagination.page);
            options.params = options.params.append("size", pagination.per_page);
        }
        return this.httpClient.get<Page>(this.END_POINT, options);
    }


}