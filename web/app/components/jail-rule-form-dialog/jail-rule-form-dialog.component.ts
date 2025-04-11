import {Component, Inject, OnInit} from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import {AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {Bind} from 'app/models/service';
import {MatSelectModule} from '@angular/material/select';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatChipsModule} from '@angular/material/chips';
import {JailRule} from "../../models/jail";

@Component({
    selector: 'app-jail-rule-form-dialog',
    templateUrl: './jail-rule-form-dialog.component.html',
    standalone: true,
    imports: [ReactiveFormsModule, CommonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatChipsModule,
        MatIconModule, MatSelectModule, MatCheckboxModule

    ],
})
export class JailRuleFormDialogComponent implements OnInit {

    _fields: string[] = ['src.header', 'src.request_line', 'status_code']

    form = new FormGroup({
        field: new FormControl<string>(''),
        regex: new FormControl<string>(''),
    });

    constructor(
        private dialogRef: MatDialogRef<any>,
        @Inject(MAT_DIALOG_DATA) public ruleData: JailRule,
    ) {

    }

    ngOnInit(): void {
        this.form.get('field')?.setValue(this.ruleData.field);
        this.form.get('regex')?.setValue(this.ruleData.regex);
    }

    onCancel() {
        this.dialogRef.close();
    }

    onSubmit() {
        if (this.form.status === "INVALID") {
            return;
        }
        let data = this.form.value as Bind;


        this.dialogRef.close(data);
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }


}