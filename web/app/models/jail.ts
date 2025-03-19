export interface JailEntry {
    ipaddr: string;
    banned_on: Date;
}

export interface JailRule {
    field: string;
    regex: string;
}


export interface Jail {
    _id: string;
    name: string;
    type: string; // static,dinamic
    content: Array<JailEntry>;
    bantime: number;
    occurrence: number;
    interval: number; //seconds
    rules: Array<JailRule>;
}