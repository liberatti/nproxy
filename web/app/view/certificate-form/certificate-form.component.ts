import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { FormGroup, Validators, FormControl, AbstractControl, ReactiveFormsModule } from '@angular/forms';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatDialog } from '@angular/material/dialog';
import { Certificate, CertificateProviderType } from 'app/models/certificate';
import { NotificationService } from 'app/services/notification.service';
import { CommonModule } from '@angular/common';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSortModule } from '@angular/material/sort';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslateModule } from '@ngx-translate/core';
import { CertificateService } from 'app/services/certificate.service';

@Component({
    selector: 'app-certificate-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './certificate-form.component.html'
})

export class CertificateFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    displayedColumns: string[] = ['name', 'sans', 'action'];
    dataSource: MatTableDataSource<Certificate>;
    _supportedProviders = Object.keys(CertificateProviderType);

    sansForm = new FormGroup({
        cn: new FormControl<string>('')
    });

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),
        chain: new FormControl<string>(''),
        certificate: new FormControl<string>(''),
        private_key: new FormControl<string>(''),
        password: new FormControl<string>(''),
        not_before: new FormControl<Date>(new Date()),
        not_after: new FormControl<Date>(new Date()),
        provider: new FormControl<CertificateProviderType>(CertificateProviderType.EXTERNAL),
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private certificateService: CertificateService,
        private confirmDialog: MatDialog
    ) {
        this.dataSource = new MatTableDataSource<Certificate>;
        this.isAddMode = false;
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.isAddMode) {
            this.certificateService.getById(this.route.snapshot.params['id']).subscribe(data => {
                this.form.get('_id')?.setValue(data._id);
                this.form.get('name')?.setValue(data.name);
                this.form.get('chain')?.setValue(data.chain);
                this.form.get('certificate')?.setValue(data.certificate);
                this.form.get('private_key')?.setValue(data.private_key);
                this.form.get('not_before')?.setValue(data.not_before);
                this.form.get('not_after')?.setValue(data.not_after);
                this.form.get('provider')?.setValue(data.provider);
            });
        }
    }
    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Certificate;

        if (this.isAddMode) {
            Reflect.deleteProperty(formData, '_id');
            this.certificateService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('Certificate saved');
                this.router.navigate(['/certificate']);
            });
        } else {
            this.certificateService.update(formData._id, formData).subscribe(() => {
                this.notificationService.openSnackBar('Certificate updated');
                this.router.navigate(['/certificate']);
            });
        }
    }

    onRemove(selectedIndex: number) {
        const data = this.dataSource.data;
        data.splice(selectedIndex, 1);
        this.dataSource.data = data;
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }
}