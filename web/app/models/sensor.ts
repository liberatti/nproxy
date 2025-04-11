import {Feed} from "./feed";
import {Jail} from "./jail";

export interface RuleCategory {
    _id: string;
    name: string;
    rules: Array<SecRule>;
    mandatory: boolean;
}

export interface SecRule {
    schema_type: string;
    code: number;
    msg: string;
    action: string;
    active: boolean;
    phase: string;
    logging: string;
    auditLog: string;
    comment: string;
    condition: string;
    scope: string;
}

export interface Sensor {
    _id: string;
    name: string;
    description: string;
    block: Array<Feed>;
    permit: Array<Feed>;
    geo_block_list: string[];
    jails: Array<Jail>;
    categories: Array<string>;
    exclusions: Array<number>;
}

export interface SecRuleCustom {
    code: number;
    active: boolean;
    logging: boolean;
    auditLog: boolean;
    action: string;
}