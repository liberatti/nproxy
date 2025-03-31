import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
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
import {RuleCategory, SecRule, Sensor} from 'app/models/sensor';
import {RuleCategoryService, SensorService} from 'app/services/sensor.service';
import {NotificationService} from 'app/services/notification.service';
import {DefaultPageMeta, PageMeta} from 'app/models/shared';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatTabsModule} from '@angular/material/tabs';
import {MatGridListModule} from '@angular/material/grid-list';
import {OAuthService} from "../../services/oauth.service";
import {Feed} from "../../models/feed";
import {FeedService} from "../../services/feed.service";
import {FilterSelectedModelPipe} from "../../pipes/filter_selected_model.pipe";

@Component({
    selector: 'app-sensor-form',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, MatTabsModule, MatGridListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule, MatCheckboxModule,
        MatFormFieldModule, MatChipsModule, FilterSelectedModelPipe],
    templateUrl: './sensor-form.component.html'
})

export class SensorFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    breakpoint: number;
    _categories: RuleCategory[] = [];
    _rbl_feeds: Feed[] = [];
    ruleDC: string[] = ['code', 'severity', 'msg', 'actionSummary', 'action'];
    ruleDS: MatTableDataSource<SecRule>;
    ruleCH: number[] = [];

    form = new FormGroup({
        _id: new FormControl<string>(''),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ],
        }),
        description: new FormControl<string>(''),
        categories: new FormControl<Array<string>>([]),
        exclusions: new FormControl<Array<number>>([]),
        block: new FormControl<Array<Feed>>([]),
        permit: new FormControl<Array<Feed>>([]),
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private sensorService: SensorService,
        private ruleCatService: RuleCategoryService,
        private feedService: FeedService,
        protected oauth: OAuthService
    ) {
        this.breakpoint = (window.innerWidth <= 600) ? 2 : 8;
        this.isAddMode = false;
        this.ruleDS = new MatTableDataSource<SecRule>;
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.oauth.isRole('superuser')) {
            this.form.disable();
        }
        if (!this.isAddMode) {
            this.sensorService.getById(this.route.snapshot.params['id']).subscribe(data => {
                this.form.get('_id')?.setValue(data._id);
                this.form.get('name')?.setValue(data.name);
                this.form.get('description')?.setValue(data.description);
                this.form.get('categories')?.setValue(data.categories);
                this.form.get('exclusions')?.setValue(data.exclusions);
                this.form.get('block')?.setValue(data.block);
                this.form.get('permit')?.setValue(data.permit);
            });
        }
        this.getCategories(null);
        this.getFeeds(null);
    }

    onSave(preview: boolean) {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Sensor;

        if (formData.block) {
            for (let i = 0; i < formData.block.length; i++) {
                formData.block[i] = {_id: formData.block[i]._id} as Feed;
            }
        }
        if (formData.permit) {
            for (let i = 0; i < formData.permit.length; i++) {
                formData.permit[i] = {_id: formData.permit[i]._id} as Feed;
            }
        }
        if (this.isAddMode) {
            Reflect.deleteProperty(formData, '_id');
            this.sensorService.save(formData).subscribe(() => {
                this.notificationService.openSnackBar('Sensor saved');
                this.router.navigate(['/sensor']);
            });
        } else {
            this.sensorService.update(formData._id, formData).subscribe(() => {
                this.notificationService.openSnackBar('Sensor updated');
                this.router.navigate(['/sensor']);
            });
        }
    }

    isRuleSelected(code: number): boolean {
        for (let i = 0; i < this.ruleCH.length; i++) {
            if (this.ruleCH[i] === code) {
                return true;
            }
        }
        return false;
    }

    selectRule(checked: boolean, code: number) {
        if (checked) {
            this.ruleCH.push(code);
        } else {
            let idx = this.ruleCH.indexOf(code);
            this.ruleCH.splice(idx, 1);
        }
    }

    selectAllRules(checked: boolean) {
        if (checked) {
            for (let i = 0; i < this.ruleDS.data.length; i++) {
                if (!this.ruleCH.includes(this.ruleDS.data[i].code)) {
                    this.ruleCH.push(this.ruleDS.data[i].code);
                }
            }
        } else {
            this.ruleCH = [];
        }
    }

    getFeeds(event: any) {
        if (event === null) {
            this.feedService.get(new DefaultPageMeta()).subscribe(data => {
                this._rbl_feeds = data.data.filter(item => item['type'] === 'network');
            });
        } else
            this.feedService.getByName(event.target.value, <PageMeta>{per_page: 100, page: 0}).subscribe(data => {
                this._rbl_feeds = data.data;
            });
    }

    onAddBlock(event: any): void {
        let data = event.value as Feed;
        if (this.form.value.block != null) {
            this.form.value.block.push(data);
        }
    }

    onAddPermit(event: any): void {
        let data = event.value as Feed;
        if (this.form.value.permit != null) {
            this.form.value.permit.push(data);
        }
    }

    onRemovePermit(keyword: any): void {
        if (this.form.value.permit != null) {
            let index = this.form.value.permit.indexOf(keyword);
            if (index >= 0) {
                this.form.value.permit.splice(index, 1);
            }
        }
    }

    onRemoveBlock(keyword: any): void {
        if (this.form.value.block != null) {
            let index = this.form.value.block.indexOf(keyword);
            if (index >= 0) {
                this.form.value.block.splice(index, 1);
            }
        }
    }


    getCategories(event: any) {
        let phases = [3, 5]
        if (event === null) {
            this.ruleCatService.getByPhases(phases).subscribe(data => {
                this._categories = data;
            });
        } else
            this.ruleCatService.getByNameAndPhases(event.target.value, phases).subscribe(data => {
                this._categories = data;
            });
    }

    onAddCategory(event: any): void {
        let data = event.value as RuleCategory;
        if (this.form.value.categories != null) {
            this.form.value.categories.push(data.name);
        }
    }

    onSelectCategory(cat_name: string): void {
        this.ruleCatService.getBySingleName(cat_name).subscribe(data => {
            let rules = [];
            for (let i = 0; i < data.rules.length; i++) {
                const rule = data.rules[i];
                if (rule.action === "block") {
                    rules.push(rule);
                }
            }
            this.ruleDS.data = rules;
            this.ruleCH = [];
        });
    }

    onRemoveCategory(keyword: any): void {
        if (this.form.value.categories != null) {
            let index = this.form.value.categories.indexOf(keyword);
            if (index >= 0) {
                this.form.value.categories.splice(index, 1);
            }
        }
    }

    isRuleActive(code: number) {
        let exclusions = this.form.value.exclusions as Array<number>;
        return !exclusions.includes(code);
    }

    onRuleCheck(checked: boolean, code: number) {
        let exclusions = this.form.value.exclusions as Array<number>;
        if (checked) {
            exclusions.splice(exclusions.indexOf(code), 1);
        } else {
            if (!exclusions.includes(code)) {
                exclusions.push(code);
            }
        }
        this.form.get('exclusions')?.reset(exclusions);
    }

    filterActive(arr1: Array<any>, arr2: Array<any> | null | undefined): Array<any> {
        if (arr1 && arr2)
            return arr1.filter(itemA => !arr2.some(itemB => itemB == itemA['name']));
        return arr1;
    }


    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }
}
