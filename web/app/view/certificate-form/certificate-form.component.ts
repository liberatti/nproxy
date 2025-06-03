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
        provider: new FormControl<CertificateProviderType>(CertificateProviderType.MANAGED),
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
        // Extract id from route params
        const { id } = this.route.snapshot.params;
        this.isAddMode = !id;

        // Disable form if user is not a superuser
        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
            // No need to fetch data if form is disabled and not in add mode
            if (!this.isAddMode) return;
        }

        // If editing, fetch certificate and patch form values
        if (!this.isAddMode) {
            this.certificateService.getById(id).subscribe(data => {
                this.form.patchValue({
                    _id: data._id,
                    name: data.name,
                    chain: data.chain,
                    certificate: data.certificate,
                    private_key: data.private_key,
                    not_before: data.not_before,
                    not_after: data.not_after,
                    provider: data.provider
                });
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