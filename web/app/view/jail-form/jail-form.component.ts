import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule} from '@angular/forms';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
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
import {Jail, JailEntry, JailRule} from 'app/models/jail';
import {JailService} from 'app/services/jail.service';
import {NotificationService} from 'app/services/notification.service';
import {JailRuleFormDialogComponent} from "../../components/jail-rule-form-dialog/jail-rule-form-dialog.component";
import {MatDialog} from "@angular/material/dialog";
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-jail-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './jail-form.component.html'
})
export class JailFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    ruleDS: MatTableDataSource<JailRule>;
    ruleDC: string[] = ['field', 'regex', 'action'];

    contentForm = new FormGroup({
        text: new FormControl<string>('')
    });

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>(''),
        content: new FormControl<Array<JailEntry>>([]),
        bantime: new FormControl<number>(60),
        occurrence: new FormControl<number>(1),
        interval: new FormControl<number>(1),
        rules: new FormControl<Array<JailRule>>([]),
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private jailService: JailService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.ruleDS = new MatTableDataSource<JailRule>;
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

        // If editing, fetch jail and patch form values
        if (!this.isAddMode) {
            this.jailService.getById(id).subscribe(data => {
                this.form.patchValue({
                    _id: data._id,
                    name: data.name,
                    content: data.content,
                    bantime: data.bantime,
                    occurrence: data.occurrence,
                    interval: data.interval,
                    rules: data.rules
                });
                // Update rules data source
                this.ruleDS.data = data.rules;
            });
        }
    }

    onSubmit() {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Jail;

        if (this.isAddMode) {
            Reflect.deleteProperty(formData, '_id');
            this.jailService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('Jail saved');
                this.router.navigate(['/jail']);
            });
        } else {

            this.jailService.update(formData._id, formData).subscribe(() => {
                this.notificationService.openSnackBar('Jail updated');
                this.router.navigate(['/jail']);
            });
        }
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }

    onAddContent(): void {
        const formData = this.contentForm.value.text as string;
        if (this.form.value.content != null) {
            this.form.value.content?.push({"ipaddr": formData} as JailEntry);
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

    onRuleRemove(index: number) {
        const data = this.ruleDS.data;
        data.splice(index, 1);
        this.ruleDS.data = data;
    }

    onAddRule() {
        const dialogRef = this.confirmDialog.open(JailRuleFormDialogComponent, {
            width: '450px',
            data: {
                bind: {} as JailRule
            }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.ruleDS.data;
                data.push(result);
                this.ruleDS.data = data;
                this.form.get('rules')?.reset(data);
            }
        });
    }

    onEditRule(index: number) {

        const dialogRef = this.confirmDialog.open(JailRuleFormDialogComponent,
            {
                maxWidth: undefined,
                data: this.ruleDS.data[index]
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.onRuleRemove(index);
                const data = this.ruleDS.data;
                data.push(result);
                this.ruleDS.data = data;
                this.form.get('rules')?.reset(data);
            }
        });

    }

}