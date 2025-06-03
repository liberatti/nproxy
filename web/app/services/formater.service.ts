import {Injectable, Injector} from '@angular/core';
import {LocalStorageService} from './localstorage.service';
import moment from 'moment';
import {API_DATA_FORMAT} from "../app.config";

interface Abbreviations {
    [key: string]: number;
}

@Injectable({
    providedIn: 'root'
})
export class FormaterService {

    private config;
    protected DEFAULT_API_DATA_FORMAT: string;

    constructor(private injector: Injector,
                private localstorage: LocalStorageService
    ) {
        this.config = this.localstorage.get("ui_config");
        this.DEFAULT_API_DATA_FORMAT = injector.get(API_DATA_FORMAT)
    }


    filterActive(list1: any[], list2: any[] | null | undefined): any[] {
        if (list1 && list2)
            return list1.filter(item1 =>
                !list2?.some(item2 => item2._id === item1._id)
            );
        return []
    }


    byte(bytes: number, precision: number = 2): string {
        if (isNaN(parseFloat(String(bytes))) || !isFinite(bytes)) return 'N/A';

        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const base = 1024;

        let i = 0;
        while (bytes >= base && i < sizes.length - 1) {
            bytes /= base;
            i++;
        }

        return bytes.toFixed(precision) + ' ' + sizes[i];
    }

    timestamp(value: Date, format: string = ''): string {
        if (value) {
            if (format === '') {
                let _conf = this.localstorage.get("ui_config");
                if (!_conf) {
                    format = this.DEFAULT_API_DATA_FORMAT;
                } else
                    format = _conf.display.datetime;
            }
            return moment(value).format(format);
        }
        return value;
    }

    counter(value: number): string {
        if (isNaN(value) || !isFinite(value)) return 'N/A';

        const abs = Math.abs(value);
        const rounder = Math.pow(10, 2);
        const isNegative = value < 0;

        let key: string = '';
        let valueFormatted: string = '';

        const abbreviations: Abbreviations = {
            'K': 1e3,
            'M': 1e6,
            'B': 1e9,
            'T': 1e12,
        };

        for (const s in abbreviations) {
            if (abs >= abbreviations[s]) {
                key = s;
                valueFormatted = String((Math.round(value / abbreviations[s] * rounder) / rounder).toFixed(0));
            }
        }

        if (key === '') {
            valueFormatted = String((Math.round(value * rounder) / rounder).toFixed(0));
            return valueFormatted;
        } else {
            return (isNegative ? '-' : '') + valueFormatted + key;
        }
    }

    tpm(value: number): string {
        if (isNaN(value) || !isFinite(value)) return 'N/A';

        const abs = Math.abs(value);
        const rounder = Math.pow(10, 0);
        const isNegative = value < 0;

        let key: string = '';
        let valueFormatted: string = '';

        const abbreviations: Abbreviations = {
            'K tpm': 1e3,
            'M tpm': 1e6,
            'B tpm': 1e9,
            'T tpm': 1e12,
        };

        for (const symbol in abbreviations) {
            if (abs >= abbreviations[symbol]) {
                key = symbol;
                valueFormatted = String((Math.round(value / abbreviations[symbol] * rounder) / rounder).toFixed(0));
            }
        }

        if (key === '') {
            valueFormatted = String((Math.round(value * rounder) / rounder).toFixed(0));
            return valueFormatted;
        } else {
            return (isNegative ? '-' : '') + valueFormatted + key;
        }
    }

    time(value: number): string {
        if (isNaN(value) || !isFinite(value)) return 'N/A';

        const abs = Math.abs(value);
        const isNegative = value < 0;

        const timeUnits: { [key: string]: number } = {
            'ms': 1,
            's': 1000,
            'min': 60 * 1000,
            'h': 60 * 60 * 1000,
            'd': 24 * 60 * 60 * 1000,
        };

        let key = '';
        let valueFormatted = '';

        for (const unit in timeUnits) {
            if (abs >= timeUnits[unit]) {
                key = unit;
                valueFormatted = String((Math.round(value / timeUnits[unit]) * timeUnits[unit]).toFixed(2));
            }
        }
        if (key === '') {
            key = 'ms'
            valueFormatted = String(Math.round(value).toFixed(2));
        }
        return (isNegative ? '-' : '') + valueFormatted + key;
    }
}