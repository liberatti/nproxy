export interface Feed {
    _id: string;
    name: string;
    action: string; // deny, pass
    slug: string;
    type: string; //network, ruleset, network_static
    scope: string; //system, user
    description: string;
    provider: string;
    version: string;
    content: [];
    source: string;
    update_interval: string;
    updated_on: Date;
}

export interface GeoCountry {
    code: string;
    name: string;
}