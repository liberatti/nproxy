import {HttpClient} from '@angular/common/http';
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
import {Router, RouterModule} from '@angular/router';
import {User} from 'app/models/oauth';
import {Language} from 'app/models/shared';
import {LocalStorageService} from 'app/services/localstorage.service';
import {NotificationService} from 'app/services/notification.service';
import {OAuthService} from 'app/services/oauth.service';
import {NgOptimizedImage} from "@angular/common";

@Component({
    selector: 'app-sign-in',
    standalone: true,
    imports: [RouterModule, FormsModule, ReactiveFormsModule,
        MatIconModule, MatButtonModule, MatFormFieldModule,
        MatCardModule, MatProgressBarModule, MatInputModule,
        MatTooltipModule, MatSelectModule, MatOptionModule, MatGridListModule, NgOptimizedImage
    ],

    templateUrl: './sign-in.component.html',
    styleUrl: './sign-in.component.css'
})
export class SignInComponent implements OnInit {
    locales = [] as Array<Language>;

    form = new FormGroup({
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
        locale: new FormControl<string>('en_US'),
    });

    constructor(private router: Router,
                private auth: OAuthService, private http: HttpClient,
                private localStorage: LocalStorageService,
                private notificationService: NotificationService) {
    }

    ngOnInit() {
        this.logout();
        this.locales = [
            {id: 'en_US', name: "English (US)"}
        ];
    }

    login() {
        if (this.form.status === "INVALID") {
            return;
        }
        const formData = this.form.value as User;
        this.auth.login(formData).subscribe({
            next: (data) => {
                this.auth.storeTokens(data);
                this.router.navigate(['/dashboard']).then(r => true);
            },
            error: (err) => {
                this.notificationService.openSnackBar("Authentication failed")
                this.router.navigate(['/signin']).then(r => true);
            }
        });
    }

    logout() {
        this.auth.logout();
        this.localStorage.remove('oidc');
    }
}
