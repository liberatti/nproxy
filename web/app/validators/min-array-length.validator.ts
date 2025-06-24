import { AbstractControl, ValidationErrors } from '@angular/forms';

export function minArrayLength(min: number) {
  return (control: AbstractControl): ValidationErrors | null => {
    if (Array.isArray(control.value) && control.value.length >= min) {
      return null;
    }
    return {
      minArrayLength: {
        requiredLength: min,
        actualLength: control.value ? control.value.length : 0
      }
    };
  };
} 