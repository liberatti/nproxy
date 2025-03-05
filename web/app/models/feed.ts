export interface Feed {
    _id: string;
    name: string;
    slug: string;
    type: string; //network, ruleset
    scope: string; //system, user
    description: string;
    provider: string;
    version: string;
    source: string;
    update_interval: string;
    updated_on: Date;
}
