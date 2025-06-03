import {ProtocolType, SessionPersistenceEntity} from "./service";

export interface Upstream {
    _id: string;
    name: string;
    script_path: string; //fastcgi
    type: string; // backend, static
    description: string;
    protocol: ProtocolType;
    retry: number;
    retry_timeout: number;
    conn_timeout: number;
    targets: [];
    persist: SessionPersistenceEntity;
    index: string;
}

export interface UpstreamTargetStatus {
    endpoint: string;
    healthy: boolean;
}

export interface UpstreamStatus {
    _id: string;
    name: string;
    healthy: boolean;
    targets: UpstreamTargetStatus[];
}

export interface NodeStatus {
    _id: string;
    name: string;
    scn: string;
    version: string;
    role: string;
    net_send: number;
    net_recv: number;
    healthy: boolean;
    last_check: Date;
    upstreams: UpstreamStatus[]
}