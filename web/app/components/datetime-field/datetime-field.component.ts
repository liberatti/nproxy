import { Component, forwardRef, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';
import moment from 'moment';

@Component({
  selector: 'app-datetime-field',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatMomentDateModule,
    MatIconModule,
    MatButtonModule,
    MatSelectModule
  ],
  templateUrl: './datetime-field.component.html',
  styleUrls: ['./datetime-field.component.css'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => DatetimeFieldComponent),
      multi: true
    }
  ]
})
export class DatetimeFieldComponent implements ControlValueAccessor {
  @Input() label = 'Data e Hora';
  @Input() placeholder = 'Selecione a data e hora';
  @Output() confirm = new EventEmitter<Date>();
  disabled = false;
  datetimeValue: any = moment();
  dateInput: Date = new Date();
  hours = Array.from({length: 24}, (_, i) => i.toString().padStart(2, '0'));
  minutes = Array.from({length: 60}, (_, i) => i.toString().padStart(2, '0'));
  seconds = Array.from({length: 60}, (_, i) => i.toString().padStart(2, '0'));

  selectedHour = '00';
  selectedMinute = '00';
  selectedSecond = '00';

  private onChange: any = () => {};
  private onTouched: any = () => {};

  writeValue(value: Date | null): void {
    if (value) {
      this.datetimeValue = moment(value);
      this.dateInput = this.datetimeValue.toDate();
      this.selectedHour = this.datetimeValue.format('HH');
      this.selectedMinute = this.datetimeValue.format('mm');
      this.selectedSecond = this.datetimeValue.format('ss');
    }
  }

  onDateChange(event: any): void {
    if (event && event.value) {
      this.dateInput = event.value;
    }
  }

  onTimeChange(): void {
    this.updateValue();
  }

  onConfirm(): void {
    this.updateValue();
  }

  private updateValue(): void {
    this.datetimeValue = moment.utc(this.dateInput)
      .hours(parseInt(this.selectedHour))
      .minutes(parseInt(this.selectedMinute))
      .seconds(parseInt(this.selectedSecond))
      .milliseconds(0);
    this.confirm.emit(this.datetimeValue);
    this.onChange(this.datetimeValue);
    this.onTouched();
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  displayDateTime(date: Date | null): string {
    return date ? new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).format(date) : '';
  }
} 