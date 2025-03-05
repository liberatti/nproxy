import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { FormGroup, FormControl, AbstractControl, ReactiveFormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatDialog } from '@angular/material/dialog';
import { ConfigService } from 'app/services/config.service';
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
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { Config } from 'app/models/config';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';

@Component({
    selector: 'app-config-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule, MatTabsModule,MatExpansionModule],
    templateUrl: './config-form.component.html',
    styleUrl: './config-form.component.css'
})
export class ConfigFormComponent implements OnInit {
    submitted = false;
    form = new FormGroup({
        _id: new FormControl<string>(''),
        maxmind_key: new FormControl<string>(''),
        ca_certificate: new FormControl<string>(''),
        ca_private: new FormControl<string>(''),
        acme_directory_url: new FormControl<string>(''),
        archive: new FormGroup({
            enabled: new FormControl<boolean>(false),
            archive_after: new FormControl<number>(1800),
            type: new FormControl<string>('opensearch'),
            url: new FormControl<string>(''),
            username: new FormControl<string>(''),
            password: new FormControl<string>(''),
        }),
        purge: new FormGroup({
            enabled: new FormControl<boolean>(false),
            purge_after: new FormControl<number>(1800)
        })
    });

    constructor(
        private notificationService: NotificationService,
        private router: Router,
        private configService: ConfigService
    ) {
    }

    ngOnInit(): void {
        this.configService.getActive().subscribe(data => {
            this.form.get('_id')?.setValue(data._id);
            this.form.get('maxmind_key')?.setValue(data.maxmind_key);
            this.form.get('ca_certificate')?.setValue(data.ca_certificate);
            this.form.get('ca_private')?.setValue(data.ca_private);
            this.form.get('acme_directory_url')?.setValue(data.acme_directory_url);
            if (data.archive)
                this.form.get('archive')?.setValue(data.archive);
            if(data.purge)
            this.form.get('purge')?.setValue(data.purge);

        });

    }
    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Config;
        this.configService.update(formData._id, formData).subscribe({
            next: (data) => {
                this.notificationService.openSnackBar('Config updated');
                this.router.navigate(['/config']);
            },
            error: (err) => {
                this.notificationService.openSnackBar("Config failed, " + err.message);
            }
        });
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}