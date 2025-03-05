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
import {Jail, JailEntry} from 'app/models/jail';
import {JailService} from 'app/services/jail.service';
import {NotificationService} from 'app/services/notification.service';
import {DateFormatPipe} from "../../pipes/date_format.pipe";

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
        MatFormFieldModule, MatChipsModule, DateFormatPipe],
    templateUrl: './jail-form.component.html'
})
export class JailFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;

    jailDC: string[] = ['name', 'sans', 'action'];
    jailDS: MatTableDataSource<Jail>;
    contentForm = new FormGroup({
        text: new FormControl<string>('')
    });

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>(''),
        content: new FormControl<Array<JailEntry>>([]),
        bantime: new FormControl<number>(60),

    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private jailService: JailService,
    ) {
        this.jailDS = new MatTableDataSource<Jail>;
        this.isAddMode = false;
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.isAddMode) {
            this.jailService.getById(this.route.snapshot.params['id']).subscribe(data => {
                this.form.get('_id')?.setValue(data._id);
                this.form.get('name')?.setValue(data.name);
                this.form.get('content')?.setValue(data.content);
                this.form.get('bantime')?.setValue(data.bantime);
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

    onRemove(selectedIndex: number) {
        const data = this.jailDS.data;
        data.splice(selectedIndex, 1);
        this.jailDS.data = data;
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
}