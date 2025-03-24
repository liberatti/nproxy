import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
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
    _supportedTypes = ['network', 'ruleset'];

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
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
        }
        if (!this.isAddMode) {
            this.feedService.getById(this.route.snapshot.params['id']).subscribe(data => {
                this.form.get('_id')?.setValue(data._id);
                this.form.get('name')?.setValue(data.name);
                this.form.get('scope')?.setValue(data.scope);
                this.form.get('type')?.setValue(data.type);
                this.form.get('description')?.setValue(data.description);
                this.form.get('slug')?.setValue(data.slug);
                this.form.get('provider')?.setValue(data.provider);
                this.form.get('version')?.setValue(data.version);
                this.form.get('source')?.setValue(data.source);
                this.form.get('update_interval')?.setValue(data.update_interval);
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

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }
}