import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Upstream} from "../models/upstream";

@Injectable({
    providedIn: 'root'
})
export class UpstreamService extends APIService<Upstream, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'upstream')
    }
}
