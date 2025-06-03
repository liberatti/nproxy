import { Pipe, PipeTransform } from '@angular/core';
import { FormaterService } from '../services/formater.service';

@Pipe({
  name: 'timeFormat',standalone: true
})
export class TimeFormatPipe implements PipeTransform {
  constructor(private formater: FormaterService) { }

  transform(value: number): string {
    if (isNaN(value) || !isFinite(value)) return 'N/A';
    return this.formater.time(value);
  }
}