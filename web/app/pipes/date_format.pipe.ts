import { Pipe, PipeTransform } from '@angular/core';
import { FormaterService } from '../services/formater.service';

@Pipe({
    name: 'dateFormat',standalone: true,
})
export class DateFormatPipe implements PipeTransform {
    constructor(private formater: FormaterService) { }

    transform(value: any, format: string = ''): string {
        if (value) {
            return this.formater.timestamp(value, format);
        }
        return value;
    }
}