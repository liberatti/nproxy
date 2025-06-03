import {Component, OnInit} from '@angular/core';
import {MatDialogActions, MatDialogContent, MatDialogRef, MatDialogTitle} from '@angular/material/dialog';
import {AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {Header} from 'app/models/service';

@Component({
    selector: 'app-service-header-form-dialog',
    templateUrl: './service-header-form-dialog.component.html',
    standalone: true,
    imports: [ReactiveFormsModule, CommonModule,
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

export class ServiceHeaderFormDialogComponent implements OnInit {
    form = new FormGroup({
        name: new FormControl<string>('', {
        }),
        content: new FormControl<string>('', {
        }),
    });
    constructor(
        private dialogRef: MatDialogRef<any>
    ) { }

    ngOnInit(): void { }
    onCancel() {
        this.dialogRef.close();
    }
    onSubmit() {
        if (this.form.status === "INVALID") {
            return;
        }
        const data = this.form.value as Header;
        this.dialogRef.close(data);
    }
    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}