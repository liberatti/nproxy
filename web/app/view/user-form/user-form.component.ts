import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {Feed} from 'app/models/feed';
import {NotificationService} from 'app/services/notification.service';
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
import {OAuthService, UserService} from "../../services/oauth.service";

@Component({
    selector: 'app-user-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, ScrollingModule, MatListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './user-form.component.html'
})
export class UserFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    _supportedRoles = ['viewer', 'superuser'];

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),
        email: new FormControl<string>(''),
        role: new FormControl<string>(''),
        password: new FormControl<string>(''),
        cpassword: new FormControl<string>('')
    });


    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private feedService: UserService,
        protected oauth: OAuthService
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

        // If editing, fetch user and patch form values
        if (!this.isAddMode) {
            this.feedService.getById(id).subscribe(data => {
                this.form.patchValue({
                    _id: data._id,
                    name: data.name,
                    email: data.email,
                    role: data.role,
                    password: data.password
                });
            });
        }
    }

    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Feed;


        if (this.isAddMode) {
            Reflect.deleteProperty(formData, '_id');
            this.feedService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('User saved');
                this.router.navigate(['/users']);
            });
        } else {
            this.feedService.update(formData._id, formData).subscribe(() => {
                this.notificationService.openSnackBar('User updated');
                this.router.navigate(['/users']);
            });
        }
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}