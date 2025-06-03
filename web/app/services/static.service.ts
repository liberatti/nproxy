import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {StaticServer} from "../models/static";
import {Observable} from "rxjs";

@Injectable({
    providedIn: 'root'
})
export class StaticService extends APIService<StaticServer, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'static')
    }
    saveAndUpload(data: FormData): Observable<any> {
        return this.httpClient.post<any>(this.END_POINT, data);
    }
    updateAndUpload(id:String,data: FormData): Observable<any> {
        return this.httpClient.put<any>(this.END_POINT + "/" + id, data);
    }
}