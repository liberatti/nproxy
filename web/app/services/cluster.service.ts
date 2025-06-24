import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Observable} from "rxjs";
import {Page} from "../models/shared";

@Injectable({
    providedIn: 'root'
})
export class ClusterService extends APIService<any, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'cluster')
    }
    healthCheck(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + "/health");
    }

    getPending(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + "/changes");
    }

    applyConfig(): Observable<any> {
        return this.httpClient.get<any>(this.END_POINT + "/apply");
    }

    downloadConfig(): Observable<Blob> {
        const httpOptions = {
            responseType: 'blob' as 'json'
        };
        return this.httpClient.get<Blob>(this.END_POINT + "/backup", httpOptions);
    }

    uploadConfig(data: FormData): Observable<any> {
        return this.httpClient.post<any>(this.END_POINT + "/backup", data);
    }

    getNodes(): Observable<Page> {
        return this.httpClient.get<Page>(this.END_POINT + "/nodes");
    }
}