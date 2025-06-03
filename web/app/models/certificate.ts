
export enum CertificateProviderType {
    MANAGED = 'MANAGED',
    EXTERNAL = 'EXTERNAL',
    SELF = 'SELF'
}

export interface Certificate {
    _id: string;
    name: string;
    chain: string;
    certificate: string;
    private_key: string;
    ssl_client_ca:string;
    provider: CertificateProviderType;
    not_before: Date;
    not_after: Date;
    force_renew:boolean;
}