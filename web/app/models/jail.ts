export interface JailEntry {
    ipaddr: string;
    banned_on: Date;
}
export interface Jail {
    _id: string;
    name: string;
    content: Array<JailEntry>;
    bantime: number;
}