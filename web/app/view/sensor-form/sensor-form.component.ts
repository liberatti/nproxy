import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
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
import {Dictionary} from 'app/models/dictionary';
import {RuleCategory, SecRule, Sensor} from 'app/models/sensor';
import {DictionaryService} from 'app/services/dictionary.service';
import {RuleCategoryService, SensorService} from 'app/services/sensor.service';
import {NotificationService} from 'app/services/notification.service';
import {DefaultPageMeta, PageMeta} from 'app/models/shared';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatTabsModule} from '@angular/material/tabs';
import {MatGridListModule} from '@angular/material/grid-list';

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
        MatFormFieldModule, MatChipsModule],
    templateUrl: './sensor-form.component.html'
})

export class SensorFormComponent implements OnInit {
    isAddMode: boolean;
    submitted = false;
    breakpoint: number;
    _categories: RuleCategory[] = [];
    _dictionaries: Dictionary[] = [];
    _rules: SecRule[] = [];
    ruleDC: string[] = ['code', 'severity', 'msg', 'actionSummary', 'action'];
    ruleDS: MatTableDataSource<SecRule>;
    ruleCH: number[] = [];

    catForm = new FormGroup({
        category: new FormControl<RuleCategory>(<RuleCategory>{})
    });

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
        block: new FormControl<Array<Dictionary>>([]),
        permit: new FormControl<Array<Dictionary>>([]),
    });

    constructor(
        private notificationService: NotificationService,
        private route: ActivatedRoute,
        private router: Router,
        private sensorService: SensorService,
        private ruleCatService: RuleCategoryService,
        private daoService: DictionaryService
    ) {
        this.breakpoint = (window.innerWidth <= 600) ? 2 : 8;
        this.isAddMode = false;
        this.ruleDS = new MatTableDataSource<SecRule>;
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
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
        this.getDictionaries(null);
        this.getCategories(null);
    }

    onSave(preview: boolean) {
        this.submitted = true;
        if (this.form.status === "INVALID") {
            return;
        }

        const formData = this.form.value as Sensor;

        if (formData.block) {
            for (let i = 0; i < formData.block.length; i++) {
                formData.block[i] = {_id: formData.block[i]._id} as Dictionary;
            }
        }
        if (formData.permit) {
            for (let i = 0; i < formData.permit.length; i++) {
                formData.permit[i] = {_id: formData.permit[i]._id} as Dictionary;
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

    getDictionaries(event: any) {
        if (event === null) {
            this.daoService.get(new DefaultPageMeta()).subscribe(data => {
                this._dictionaries = data.data;
            });
        } else
            this.daoService.getByName(event.target.value, <PageMeta>{per_page: 100, page: 0}).subscribe(data => {
                this._dictionaries = data.data;
            });
    }

    onAddDictionary(event: any, type: string): void {
        let data = event.value as Dictionary;
        switch (type) {
            case "p": {
                if (this.form.value.permit != null) {
                    this.form.value.permit.push(data);
                }
                break;
            }
            case "b": {
                if (this.form.value.block != null) {
                    this.form.value.block.push(data);
                }
                break;
            }
        }
    }

    onRemoveDictionary(keyword: any, type: string): void {
        switch (type) {
            case "p": {
                if (this.form.value.permit != null) {
                    let index = this.form.value.permit.indexOf(keyword);
                    if (index >= 0) {
                        this.form.value.permit.splice(index, 1);
                    }
                }
                break;
            }
            case "b": {
                if (this.form.value.block != null) {
                    let index = this.form.value.block.indexOf(keyword);
                    if (index >= 0) {
                        this.form.value.block.splice(index, 1);
                    }
                }
                break;
            }
        }


    }

    filterActiveDictionary(dic: Array<Dictionary>): Array<Dictionary> {
        const formData = this.form.value as Sensor;
        formData.block = formData.block || [];
        formData.permit = formData.permit || [];
        const selectedDictionaries: Array<Dictionary> = [];
        for (let index = 0; index < dic.length; index++) {
            const c = dic[index];
            const isInBlock = formData.block.some(item => item._id === c._id);
            const isInPermit = formData.permit.some(item => item._id === c._id);
            if (!isInBlock && !isInPermit) {
                selectedDictionaries.push(c);
            }
        }
        return selectedDictionaries;
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

    filterActive(cat: Array<RuleCategory>): Array<RuleCategory> {
        const formData = this.form.value as Sensor;
        let cats = [];
        for (let index = 0; index < cat.length; index++) {
            const c = cat[index];
            if (!formData.categories.includes(c.name)) {
                cats.push(c);
            }
        }
        return cats;
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

    onRuleGroupCheck() {
        this.form.get('exclusions')?.reset([]);
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}
