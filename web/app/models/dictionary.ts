export interface Dictionary {
    _id: string;
    name: string;
    slug: string;
    type: string;
    scope: string;
    description: string;
    content: Array<string>;
    usage: number;
}