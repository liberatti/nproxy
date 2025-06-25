import {StaticServer} from "./static";
import {Sensor} from "./sensor";
import {Upstream} from "./upstream";
import {Certificate} from "./certificate";

export enum ProtocolType {
    HTTP = 'HTTP',
    HTTPS = 'HTTPS',
    FASTCGI = 'FASTCGI',
    AJP = 'AJP'
}

export enum SessionPersistenceType {
    NONE = 'NONE',
    COOKIE = 'COOKIE',
}

export interface TargetEntity {
    host: string;
    port: number;
    weight: number;
}

export interface SessionPersistenceEntity {
    type: SessionPersistenceType;
    cookie_name: string;
    cookie_domain: string;
    cookie_path: string;
    cookie_expire: number;
}

export interface Header {
    name: string;
    content: string;
}

export interface Bind {
    port: number;
    protocol: ProtocolType;
    ssl_upgrade: boolean;
}

export interface Redirect {
    code: number;
    url: string;
}

export interface RouteFilter {
    _id: string;
    name: string;
    description: string;
    type: string; // SSL_CLIENT_AUTH, LDAP_AUTH
    ssl_dn_regex: string;
    ssl_fingerprints: string;
    ldap_host: string;
    ldap_base_dn: string;
    ldap_bind_dn: string;
    ldap_bind_password: string;
    ldap_group_dn: string;
    geo_block_list: string;
}

export interface Route {
    name: string;
    type: string;
    upstream: Upstream;
    static: StaticServer;
    redirect: Redirect;
    monitor_only: boolean;
    sensor: Sensor;
    paths: Array<string>;
    methods: Array<string>;
    cache_methods: Array<string>;
    filters: Array<RouteFilter>;
}

export interface Service {
    _id?: string;
    name: string;
    bindings: Array<Bind>
    headers: Array<Header>;
    routes: Array<Route>;
    body_limit: number;
    timeout: number;
    buffer: number;
    compression: boolean;
    compression_types: Array<string>;
    rate_limit: boolean;
    rate_limit_per_sec: number;
    sans: string[];
    ssl_protocols: Array<string>;
    certificate: Certificate;
    ssl_client_ca: string;
    ssl_client_auth: boolean;
}