import {Injectable, Injector} from '@angular/core';
import {Service} from '../models/service';
import {APIService} from './api.service';

@Injectable({
    providedIn: 'root'
})
export class ServiceService extends APIService<Service, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'service')
    }
}