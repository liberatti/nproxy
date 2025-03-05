import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Jail} from "../models/jail";

@Injectable({
    providedIn: 'root'
})
export class JailService extends APIService<Jail, string> {
    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'jail')
    }
}
