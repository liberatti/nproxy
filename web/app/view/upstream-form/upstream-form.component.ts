import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatDialog} from '@angular/material/dialog';
import {ProtocolType, SessionPersistenceEntity, SessionPersistenceType, TargetEntity} from 'app/models/service';
import {Upstream} from 'app/models/upstream';
import {UpstreamService} from 'app/services/upstream.service';
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
import {UpstreamTargetDialogComponent} from 'app/components/upstream-target-dialog/upstream-target-dialog.component';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
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
    templateUrl: './upstream-form.component.html'
})
export class UpstreamFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    _supportedProtocols = Object.keys(ProtocolType);
    _types: string[] = ['backend', 'static']
    selectedFile: File | null = null;

    targetDC: string[] = ['host', 'port', 'weight', 'action'];
    targetDS: MatTableDataSource<TargetEntity>;
    persistEnabledControl = new FormControl(false);
    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),

        script_path: new FormControl<string>('/var/www/html'),
        type: new FormControl<string>('backend'),
        description: new FormControl<string>(''),
        protocol: new FormControl<ProtocolType>(ProtocolType.HTTP),
        retry: new FormControl<number>(3),
        retry_timeout: new FormControl<number>(10),
        conn_timeout: new FormControl<number>(10),
        targets: new FormControl<Array<TargetEntity>>([]),
        persist: new FormGroup({
            type: new FormControl<SessionPersistenceType>(SessionPersistenceType.NONE),
            cookie_name: new FormControl<string>(''),
            cookie_path: new FormControl<string>('')
        }),
        index: new FormControl<string>('index.html'),
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private upstreamService: UpstreamService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.targetDS = new MatTableDataSource<any>;
        this.isAddMode = false;
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
        }
        if (!this.isAddMode) {
            this.upstreamService.getById(this.route.snapshot.params['id']).subscribe(data => {
                this.form.get('_id')?.setValue(data._id);
                this.form.get('name')?.setValue(data.name);
                this.form.get('description')?.setValue(data.description);

                this.form.get('script_path')?.setValue(data.script_path);

                if (data.type)
                    this.form.get('type')?.setValue(data.type);
                if (this.form.value.type == 'backend') {
                    this.form.get('retry')?.setValue(data.retry);
                    this.form.get('retry_timeout')?.setValue(data.retry_timeout);
                    this.form.get('conn_timeout')?.setValue(data.conn_timeout);
                    this.form.get('protocol')?.setValue(data.protocol);
                    this.targetDS.data = data.targets;
                    if (typeof data.persist != 'undefined') {
                        this.form.get('persist')?.setValue(data.persist);
                        if (data.persist.type != SessionPersistenceType.NONE) {
                            this.persistEnabledControl.setValue(true);
                        }
                    }
                } else {
                    this.form.get('index')?.setValue(data.index);
                }
            });
        }
    }

    onFileSelected(event: any): void {
        this.selectedFile = event.target.files[0];
        if (this.selectedFile && this.selectedFile.type !== 'application/zip') {
            this.notificationService.openSnackBar('Only ZIP files are allowed');
            this.selectedFile = null;
        }
    }

    onSubmit() {
        this.submitted = true;
        let formData = {} as any;

        if (this.form.status === "INVALID") {
            return;
        }

        if (this.form.value.type == 'static') {
            formData = new FormData()
            let upstream = this.form.value as Upstream;
            const jsonBlob = new Blob([JSON.stringify(upstream)], {type: 'application/json'});
            formData.append('metadata', jsonBlob, 'metadata.json');
            if (this.selectedFile) {
                formData.append('zipfile', this.selectedFile);
            }
        } else {
            this.form.get('targets')?.setValue(this.targetDS.data);
            formData = this.form.value as Upstream;
        }

        if (this.isAddMode) {
            Reflect.deleteProperty(formData, 'id');
            this.upstreamService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('Upstream saved');
                this.router.navigate(['/ups']);
            });
        } else {
            if (this.form.value._id)
                this.upstreamService.update(this.form.value._id, formData).subscribe(() => {
                    this.notificationService.openSnackBar('Upstream updated');
                    this.router.navigate(['/ups']);
                });
        }
    }

    persistChange() {
        if (this.persistEnabledControl.value) {
            this.form.get('persist')?.setValue({
                'type': SessionPersistenceType.COOKIE,
                'cookie_name': 'lb-route',
                'cookie_path': '/'
            } as SessionPersistenceEntity);
        } else {
            this.form.get('persist')?.setValue({
                'type': SessionPersistenceType.NONE,
                'cookie_name': '',
                'cookie_path': ''
            } as SessionPersistenceEntity);
        }
    }

    isPersistEnabled() {
        return this.form.value.persist?.type != SessionPersistenceType.NONE;
    }

    onAddTarget() {
        const dialogRef = this.confirmDialog.open(UpstreamTargetDialogComponent, {
            width: '450px',
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.targetDS.data;
                data.push(result);
                this.targetDS.data = data;
            }
        });
    }

    onRemove(selectedIndex: number) {
        const data = this.targetDS.data;
        data.splice(selectedIndex, 1);
        this.targetDS.data = data;
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}