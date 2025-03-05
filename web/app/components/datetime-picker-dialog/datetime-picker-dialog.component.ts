import {CommonModule} from '@angular/common';
import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {
    MatDialogModule,
    MatDialogRef
} from '@angular/material/dialog';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {ClusterService} from 'app/services/cluster.service';
import {TranslateModule} from "@ngx-translate/core";
import {
    MatDatepicker,
    MatDatepickerActions,
    MatDatepickerApply,
    MatDatepickerCancel,
    MatDatepickerInput,
    MatDatepickerModule,
    MatDatepickerToggle,
    MatDateRangeInput,
    MatDateRangePicker,
    MatEndDate,
    MatStartDate
} from "@angular/material/datepicker";
import {MatTimepickerModule} from "@angular/material/timepicker";
import moment from "moment/moment";

@Component({
    selector: 'app-datetime-picker-dialog',
    templateUrl: './datetime-picker-dialog.component.html',
    standalone: true,
    imports: [
        CommonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogModule,
        MatChipsModule,
        MatIconModule,
        TranslateModule,
        MatDatepickerModule,
        MatTimepickerModule,
        ReactiveFormsModule,
    ],
})

export class DatetimePickerDialogComponent {

    form = new FormGroup({
        startDate: new FormControl<Date>(moment().subtract(1, 'day').toDate()),
        startTime: new FormControl<Date>(moment().toDate()),
        endDate: new FormControl<Date>(moment().toDate()),
        endTime: new FormControl<Date>(moment().toDate()),
    })

    constructor(
        public dialogRef: MatDialogRef<DatetimePickerDialogComponent>,
    ) {
    }

    onSubmit():void{
        let lt_start=moment(this.form.value.startDate)
        let st = moment(this.form.value.startTime);
        lt_start.set({
            hour: st.hour(),
            minute: st.minute(),
            second: st.second(),
            millisecond: st.millisecond()
        });

        let lt_end=moment(this.form.value.endDate)
        let et = moment(this.form.value.endTime);
        lt_end.set({
            hour: et.hour(),
            minute: et.minute(),
            second: et.second(),
            millisecond: et.millisecond()
        });

        this.dialogRef.close({
            logtime_start: lt_start,
            logtime_end: lt_end,
        });
    }
}
