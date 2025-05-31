import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatTableModule} from '@angular/material/table';
import {RouteFilter} from 'app/models/service';
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
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {RoutefilterService} from "../../services/routefilter.service";
import {OAuthService} from "../../services/oauth.service";


@Component({
    selector: 'app-upstream-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './route_filter-form.component.html'
})
export class RouteFilterFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    _types: string[] = ['SSL_CLIENT_AUTH', 'LDAP_BASIC_AUTH']

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),
        type: new FormControl<string>('backend'),
        description: new FormControl<string>(''),
        ldap_group_dn: new FormControl<string>(''),
        ldap_host: new FormControl<string>(''),
        ldap_base_dn: new FormControl<string>(''),
        ldap_bind_dn: new FormControl<string>(''),
        ldap_bind_password: new FormControl<string>(''),
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private rfService: RoutefilterService,
        protected oauth: OAuthService,
    ) {
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

        // If editing, fetch route filter and patch form values
        if (!this.isAddMode) {
            this.rfService.getById(id).subscribe(data => {
                this.form.patchValue({
                    _id: data._id,
                    name: data.name,
                    description: data.description,
                    type: data.type,
                    ldap_group_dn: data.ldap_group_dn,
                    ldap_host: data.ldap_host,
                    ldap_base_dn: data.ldap_base_dn,
                    ldap_bind_dn: data.ldap_bind_dn,
                    ldap_bind_password: data.ldap_bind_password
                });
            });
        }
    }


    onSubmit() {
        this.submitted = true;
        let formData = {} as any;

        if (this.form.status === "INVALID") {
            return;
        }

        formData = this.form.value as RouteFilter;

        if (this.isAddMode) {
            Reflect.deleteProperty(formData, 'id');
            this.rfService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('Route Filter saved');
                this.router.navigate(['/route_filter']);
            });
        } else {
            if (this.form.value._id)
                this.rfService.update(this.form.value._id, formData).subscribe(() => {
                    this.notificationService.openSnackBar('Route Filter Updated');
                    this.router.navigate(['/route_filter']);
                });
        }
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}