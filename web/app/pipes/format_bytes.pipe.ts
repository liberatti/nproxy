import { Pipe, PipeTransform } from '@angular/core';
import { FormaterService } from '../services/formater.service';

@Pipe({
  name: 'byteFormat',standalone: true
})
export class ByteFormatPipe implements PipeTransform {
  constructor(private formater: FormaterService) { }

  transform(value: number, precision: number = 2): string {
    if (isNaN(value) || !isFinite(value)) return 'N/A';
    return this.formater.byte(value);
  }
}