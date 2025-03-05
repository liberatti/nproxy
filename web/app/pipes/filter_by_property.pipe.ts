import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'filterByProperty',
    standalone: true
})
export class FilterByPropertyPipe implements PipeTransform {

    transform(items: any[], property: string, value: any): any[] {
        if (!items || !property || !value) {
            return items;
        }
        return items.filter(item => item[property] === value);
    }
}
