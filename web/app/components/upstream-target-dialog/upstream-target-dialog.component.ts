import {CommonModule} from '@angular/common';
import {Component, OnInit} from '@angular/core';
import {AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatDialogActions, MatDialogContent, MatDialogRef, MatDialogTitle} from '@angular/material/dialog';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {TargetEntity} from 'app/models/service';

@Component({
    selector: 'app-upstream-target-dialog',
    templateUrl: './upstream-target-dialog.component.html',
    standalone: true,
    imports: [ReactiveFormsModule,CommonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatIconModule
    ],
})

export class UpstreamTargetDialogComponent implements OnInit {
    isAddMode: boolean;

    form = new FormGroup({
        host: new FormControl<string>(''),
        port: new FormControl<number>(80),
        weight: new FormControl<number>(100),
    });

    constructor(
        private dialogRef: MatDialogRef<any>
    ) {
        this.isAddMode = false;
    }

    ngOnInit(): void {

    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    public cancel() {
        this.dialogRef.close();
    }
    onSubmit() {
        this.dialogRef.close(this.form.value as TargetEntity);
    }
}