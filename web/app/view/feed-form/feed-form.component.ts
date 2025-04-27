import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {Feed} from 'app/models/feed';
import {NotificationService} from 'app/services/notification.service';
import {FeedService} from 'app/services/feed.service';
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
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-feed-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, ScrollingModule, MatListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './feed-form.component.html'
})
export class FeedFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    _supportedTypes = ['network', 'ruleset', 'network_static'];
    _actions = ['deny', 'pass']
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
        action: new FormControl<string>('deny'),
        content: new FormControl<Array<string>>([]),
        scope: new FormControl<string>('user'),
        type: new FormControl<string>(''),
        description: new FormControl<string>(''),
        slug: new FormControl<string>(''),
        provider: new FormControl<string>(''),
        version: new FormControl<string>(''),
        source: new FormControl<string>(''),
        update_interval: new FormControl<string>('')
    });


    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private feedService: FeedService,
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

        // If editing, fetch feed and patch form values
        if (!this.isAddMode) {
            this.feedService.getById(id).subscribe(data => {
                this.form.patchValue({
                    _id: data._id,
                    name: data.name,
                    action: data.action,
                    scope: data.scope,
                    type: data.type,
                    description: data.description,
                    slug: data.slug,
                    content: data.content,
                    provider: data.provider,
                    version: data.version,
                    source: data.source,
                    update_interval: data.update_interval
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
                this.notificationService.openSnackBar('feed saved');
                this.router.navigate(['/feed']);
            });
        } else {
            this.feedService.update(formData._id, formData).subscribe(() => {
                this.notificationService.openSnackBar('feed updated');
                this.router.navigate(['/feed']);
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

    trackByFn(index: number, item: any): number {
        return index;
    }
}