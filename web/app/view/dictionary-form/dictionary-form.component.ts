import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatDialog} from '@angular/material/dialog';
import {Dictionary} from 'app/models/dictionary';
import {NotificationService} from 'app/services/notification.service';
import {DictionaryService} from 'app/services/dictionary.service';
import {CommonModule} from '@angular/common';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSortModule} from '@angular/material/sort';
import {MatTableModule} from '@angular/material/table';
import {MatTooltipModule} from '@angular/material/tooltip';
import {TranslateModule} from '@ngx-translate/core';
import {MatChipsModule} from '@angular/material/chips';
import {ScrollingModule} from "@angular/cdk/scrolling";

@Component({
    selector: 'app-dictionary-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, ScrollingModule, MatListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './dictionary-form.component.html'
})
export class DictionaryFormComponent implements OnInit {
    isAddMode: boolean;
    isReadOnlyMode: boolean;
    submitted = false;
    _supportedTypes = ['network'];

    ipv4Pattern = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(3[0-2]|[12]?[0-9])$/;
    ipv6Pattern = /([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4})\/(12[0-8]|1[0-1][0-9]|[1-9]?[0-9])/;

    contentForm = new FormGroup({
        text: new FormControl<string>('', [
            Validators.required,
            this.ipv4OrIpv6Validator.bind(this)
        ])
    });

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),
        content: new FormControl<Array<string>>([]),
        scope: new FormControl<string>('user'),
        type: new FormControl<string>(''),
        description: new FormControl<string>('')
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private DictionaryService: DictionaryService,
        private confirmDialog: MatDialog
    ) {
        this.isAddMode = false;
        this.isReadOnlyMode = false;
    }

    ipv4OrIpv6Validator(control: FormControl): { [key: string]: boolean } | null {
        const value = control.value;

        // Verifica se o valor corresponde ao padrão IPv4 ou IPv6
        const isIpv4 = this.ipv4Pattern.test(value);
        const isIpv6 = this.ipv6Pattern.test(value);

        if (isIpv4 || isIpv6) {
            return null; // válido
        }

        return {'invalidAddress': true}; // inválido
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.isAddMode) {
            this.DictionaryService.getById(this.route.snapshot.params['id']).subscribe(data => {
                this.form.get('_id')?.setValue(data._id);
                this.form.get('name')?.setValue(data.name);
                this.form.get('scope')?.setValue(data.scope);
                this.form.get('content')?.setValue(data.content);
                this.form.get('type')?.setValue(data.type);
                this.form.get('description')?.setValue(data.description);
                if (data.scope == 'system') {
                    this.isReadOnlyMode = true;
                }
            });
        }
    }

    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Dictionary;


        if (this.isAddMode) {
            Reflect.deleteProperty(formData, '_id');
            this.DictionaryService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('Dictionary saved');
                this.router.navigate(['/dict']);
            });
        } else {
            this.DictionaryService.update(formData._id, formData).subscribe(() => {
                this.notificationService.openSnackBar('Dictionary updated');
                this.router.navigate(['/dict']);
            });
        }
    }

    onAddContent(): void {
        if (this.contentForm.status === "INVALID") {
            return;
        }
        const formData = this.contentForm.value.text as string;
        if (this.form.value.content != null) {
            this.form.value.content?.push(formData);
        }
        this.contentForm.reset();
    }

    onRemoveContent(keyword: any): void {
        if (this.form.value.content != null) {
            let index = this.form.value.content.indexOf(keyword);
            if (index >= 0) {
                this.form.value.content.splice(index, 1);
            }
        }
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }

    trackByFn(index: number, item: any): number {
        return index;
    }
}