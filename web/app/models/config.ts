
export interface ConfigArchive {
    enabled: boolean;
    archive_after: number;
    type: string;
    url: string;
    username: string;
    password: string;
}

export interface ConfigPurge {
    enabled: boolean;
    purge_after: number;
}

export interface ConfigTelemetry {
    enabled: boolean;
    url: string;
}

export interface Config {
    _id: string;
    maxmind_key: string;
    ca_certificate: string;
    ca_private: string;
    acme_directory_url: string;
    archive: ConfigArchive;
    purge: ConfigPurge;
    telemetry: ConfigTelemetry;
}
