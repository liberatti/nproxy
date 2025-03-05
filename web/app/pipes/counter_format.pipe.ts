import { Pipe, PipeTransform } from '@angular/core';
import { FormaterService } from '../services/formater.service';



@Pipe({
    standalone: true,
    name: 'counterFormat'
})
export class CounterFormatPipe implements PipeTransform {

    constructor(private formater: FormaterService) { }

    transform(value: number): string {
        if (isNaN(value) || !isFinite(value)) return 'N/A';
        return this.formater.counter(value);
    }
}
