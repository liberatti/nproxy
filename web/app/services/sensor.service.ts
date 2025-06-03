import {Injectable, Injector} from "@angular/core";
import {APIService} from "./api.service";
import {RuleCategory, SecRule, Sensor} from "../models/sensor";
import {Observable} from "rxjs";
import {HttpParams} from "@angular/common/http";
import {Page} from "../models/shared";

@Injectable({
    providedIn: 'root'
})
export class SensorService extends APIService<Sensor, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'sensor')
    }
}

@Injectable({
    providedIn: 'root'
})
export class RuleCategoryService extends APIService<RuleCategory, number> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'rulecat')
    }

    getByPhases(phases: Array<number>): Observable<Array<RuleCategory>> {
        let options = {
            params: new HttpParams().append("phases", phases.join(','))
        }
        return this.httpClient.get<Array<RuleCategory>>(this.END_POINT, options);
    }

    getBySingleName(name: string): Observable<RuleCategory> {
        return this.httpClient.get<RuleCategory>(this.END_POINT + "/by_name/" + name);
    }

    getByNameAndPhases(name: string, phases: Array<number>): Observable<Array<RuleCategory>> {
        let options = {
            params: new HttpParams()
        }
        options.params = options.params.append("name", name);
        for (let i = 0; i < phases.length; i++) {
            options.params = options.params.append("phases", phases[i]);
        }

        return this.httpClient.get<Array<RuleCategory>>(this.END_POINT, options);
    }
}

@Injectable({
    providedIn: 'root'
})
export class RuleService extends APIService<SecRule, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'rulesec')
    }

    get_by_code(rule_code: number): Observable<Page> {
        return this.httpClient.get<Page>(this.END_POINT + "/by_code/" + rule_code);
    }
}