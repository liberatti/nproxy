import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {Feed} from "../models/feed";
import {LocalStorageService} from "./localstorage.service";

@Injectable({
    providedIn: 'root'
})
export class FeedService extends APIService<Feed, string> {

    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService
    ) {
        super(injector, 'feed')
    }
}
