import {Upstream} from "./upstream";
import {Service} from "./service";
import {Sensor} from "./sensor";

export interface TransactionSecMatch {
    unique_id: string;
    server_id: string;
    match: string;
    rule_code: string;
    data: string;
    severity: string;
}

export interface TransactionProducer {
    name: string;
    connector: string;
    mode: string;
}

/** use */
export interface TransactionUserAgent {
    family: string;
    major: number;
    minor: number;
}

export interface TransactionFilter {
    start: Date;
    end: Date;
    filters?: Array<string>;
}

export interface TransactionHeader {
    name: string;
    content: string;
    certificate: string;
}

export interface TransactionHttp {
    request: TransactionRequest;
    response: TransactionResponse;
    version: string;
    duration: number;
    request_line: string;
}

export interface TransactionRequest {
    method: string;
    uri: string;
    headers: Array<TransactionHeader>;
    bytes: number;
}

export interface TransactionResponse {
    status_code: number;
    headers: Array<TransactionHeader>;
    bytes: number;
}

export interface TransactionDestination {
    ip: string;
}

export interface TransactionSource {
    ip: string;
    port: number;
    geo: TransactionGeo;
}

export interface TransactionGeo {
    addr: string;
    ans_number: string;
    country: string;
    organization: string;
    range_end: string;
    range_start: string;
    ip: string;
}

export interface TransactionLog {
    _id: string;
    action: string;
    logtime: Date;
    route_name: string;
    unique_id: string;
    server_id: string;
    http: TransactionHttp;
    destination: TransactionDestination;
    source: TransactionSource;
    user_agent: TransactionUserAgent;
    service: Service;
    upstream: Upstream;
    sensor: Sensor;
    isExpanded: boolean;
    limit_req_status: string;
    geoip_status: string;
    rbl_status: string;
    score: number;
}
