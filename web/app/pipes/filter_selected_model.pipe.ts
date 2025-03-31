import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
    name: 'filterSelectedModel',
    standalone: true
})
export class FilterSelectedModelPipe implements PipeTransform {

    transform(arr1: Array<any>, arr2: Array<any> | null | undefined, prop: string = '_id'): Array<any> {
        if (arr1 && arr2)
            return arr1.filter(itemA => !arr2.some(itemB => itemB[prop] == itemA[prop]));
        return arr1;
    }
}
