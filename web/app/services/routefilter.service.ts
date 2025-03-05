import {Injectable, Injector} from '@angular/core';
import {RouteFilter, Service} from '../models/service';
import {APIService} from './api.service';

@Injectable({
    providedIn: 'root'
})
export class RoutefilterService extends APIService<RouteFilter, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'route_filter')
    }
}