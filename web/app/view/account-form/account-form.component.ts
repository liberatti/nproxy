import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatOptionModule} from '@angular/material/core';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatTooltipModule} from '@angular/material/tooltip';
import {RouterModule} from '@angular/router';
import {User} from 'app/models/oauth';
import {OAuthService, UserService} from 'app/services/oauth.service';
import {MatTab, MatTabGroup} from "@angular/material/tabs";
import {NotificationService} from "../../services/notification.service";

@Component({
    selector: 'app-account-form',
    standalone: true,
    imports: [RouterModule, FormsModule, ReactiveFormsModule,
        MatIconModule, MatButtonModule, MatFormFieldModule,
        MatCardModule, MatProgressBarModule, MatInputModule,
        MatTooltipModule, MatSelectModule, MatOptionModule, MatGridListModule,  MatTabGroup, MatTab
    ],

    templateUrl: './account-form.component.html',
    styleUrl: './account-form.component.css'
})
export class AccountComponent implements OnInit{
    userInfo: any = {} as any;

    form = new FormGroup({
        _id: new FormControl<string>('', {
            validators: [
                Validators.required,
            ],
        }),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
            ],
        }),
        email: new FormControl<string>('', {
            validators: [
                Validators.required,
            ],
        }),
        password: new FormControl<string>('', {
            validators: [
                Validators.required,
            ],
        }),
    });

    constructor(
        private userService: UserService,
        private authService: OAuthService,
        private notificationService: NotificationService) {
    }

    ngOnInit() {
        this.userInfo = this.authService.userInfo();
        this.userService.getById(this.userInfo._id).subscribe(data => {
            this.form.get('_id')?.setValue(data._id);
            this.form.get('email')?.setValue(data.email);
            this.form.get('name')?.setValue(data.name);
        });
    }
    onSubmit() {
        const formData = this.form.value as User;
        if (this.form.status === "INVALID") {
            return;
        }

        this.userService.updateAccount(formData._id, formData).subscribe(() => {
            this.notificationService.openSnackBar('Profile updated');
        });
    }
}
