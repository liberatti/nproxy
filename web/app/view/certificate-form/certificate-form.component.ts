import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {Certificate, CertificateProviderType} from 'app/models/certificate';
import {NotificationService} from 'app/services/notification.service';
import {CommonModule} from '@angular/common';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
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
import {MatTooltipModule} from '@angular/material/tooltip';
import {TranslateModule} from '@ngx-translate/core';
import {CertificateService} from 'app/services/certificate.service';
import {OAuthService} from "../../services/oauth.service";

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
    dataSource: MatTableDataSource<Certificate>;
    _supportedProviders = Object.keys(CertificateProviderType);

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
        protected oauth: OAuthService,
    ) {
        this.dataSource = new MatTableDataSource<Certificate>;
        this.isAddMode = false;
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
        }
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
}