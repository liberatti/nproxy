import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Config} from "../models/config";
import {LocalStorageService} from "./localstorage.service";
import {Observable} from "rxjs";

@Injectable({
    providedIn: 'root'
})
export class ConfigService extends APIService<Config, string> {

    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService
    ) {
        super(injector, 'cluster')
    }

    getActive(): Observable<Config> {
        return this.httpClient.get<Config>(this.END_POINT + "/config");
    }

    override update(id: string, data: Config): Observable<Config> {
        return this.httpClient.put<Config>(this.END_POINT + "/config", data);
    }
}