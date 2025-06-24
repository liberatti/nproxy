import {Component, Inject, OnInit, ViewChild} from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import {AbstractControl, FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {Sensor} from 'app/models/sensor';
import {Route, RouteFilter} from 'app/models/service';
import {Upstream} from 'app/models/upstream';
import {UpstreamService} from 'app/services/upstream.service';
import {SensorService} from 'app/services/sensor.service';
import {CommonModule} from '@angular/common';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatChipsModule} from '@angular/material/chips';
import {MatSlideToggle} from '@angular/material/slide-toggle';
import {MatTabGroup, MatTabsModule} from '@angular/material/tabs';
import {StaticServer} from "../../models/static";
import {StaticService} from "../../services/static.service";
import {RoutefilterService} from "../../services/routefilter.service";


@Component({
    selector: 'app-service-route-form-dialog',
    templateUrl: './service-route-form-dialog.component.html',
    standalone: true,
    imports: [ReactiveFormsModule, CommonModule,
        MatFormFieldModule, MatChipsModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions, MatSlideToggle,
        MatIconModule, MatSelectModule, MatTabsModule
    ],
})

export class ServiceRouteFormDialogComponent implements OnInit {
    @ViewChild('tabGroup') tabGroup!: MatTabGroup;
    _supportedTypes: string[] = ['upstream', 'redirect']
    separatorKeysCodes = [COMMA, ENTER];
    _upstreams: Upstream[] = [];
    _sensors: Sensor[] = [];
    _filters: RouteFilter[] = [];
    isAddMode: boolean;
    submitted = false;

    pathForm = new FormGroup({
        path: new FormControl<string>('')
    });

    methodForm = new FormGroup({
        method: new FormControl<string>('')
    });
    cacheMethodForm = new FormGroup({
        cacheMethod: new FormControl<string>('')
    });

    filterForm = new FormGroup({
        filter: new FormControl<RouteFilter>({} as RouteFilter)
    });

    form = new FormGroup({
        name: new FormControl<string>(""),
        upstream: new FormControl<Upstream>(<Upstream>{}),
        static: new FormControl<StaticServer>(<StaticServer>{}),
        redirect: new FormGroup({
            code: new FormControl<number>(500),
            url: new FormControl<string>('')
        }),
        paths: new FormControl<Array<string>>([]),
        methods: new FormControl<Array<string>>(['GET', 'POST','PUT', 'PATCH', 'DELETE']),
        monitor_only: new FormControl<boolean>(false),
        sensor: new FormControl<Sensor>(<Sensor>{}),
        cache_methods: new FormControl<Array<string>>([]),
        type: new FormControl<string>("upstream"),
        filters: new FormControl<Array<RouteFilter>>([]),
    });

    constructor(
        private dialogRef: MatDialogRef<any>,
        private upstreamService: UpstreamService,
        private staticService: StaticService,
        private sensorService: SensorService,
        private routeFilterService: RoutefilterService,
        @Inject(MAT_DIALOG_DATA) public routeData: Route
    ) {
        this.isAddMode = false;
    }

    ngOnInit(): void {
        this.upstreamService.get().subscribe(data => {
            this._upstreams = data.data;
        });

        this.sensorService.get().subscribe(data => {
            this._sensors = data.data;
            if (this.isAddMode) {
                this.form.get('sensor')?.setValue(this._sensors[0]);
            }
        });
        this.routeFilterService.get().subscribe(data => {
            this._filters = data.data;
        });
        this.isAddMode = !this.routeData;
        if (!this.isAddMode) {
            this.form.get('name')?.setValue(this.routeData.name);
            this.form.get('upstream')?.setValue(this.routeData.upstream);
            this.form.get('static')?.setValue(this.routeData.static);
            this.form.get('redirect')?.setValue(this.routeData.redirect);
            this.form.get('paths')?.setValue(this.routeData.paths);
            this.form.get('methods')?.setValue(this.routeData.methods);
            this.form.get('monitor_only')?.setValue(this.routeData.monitor_only);
            this.form.get('sensor')?.setValue(this.routeData.sensor);
            this.form.get('type')?.setValue(this.routeData.type);
            if (this.routeData.cache_methods) {
                this.form.get('cache_methods')?.setValue(this.routeData.cache_methods);
            } else {
                this.form.get('cache_methods')?.setValue([]);
            }
            if (this.routeData.filters) {
                this.form.get('filters')?.setValue(this.routeData.filters);
            } else {
                this.form.get('filters')?.setValue([]);
            }
        }
    }

    onCancel() {
        this.dialogRef.close();
    }

    onSubmit() {
        if (this.form.status === "INVALID") {
            return;
        }
        let data = this.form.value as Route;
        this.dialogRef.close(data);
    }

    onAddPath(): void {
        let data = this.pathForm.value.path as string;
        this.form.value.paths?.push(data);
        this.pathForm.reset();
    }

    onRemovePath(keyword: any): void {
        if (this.form.value.paths != null) {
            let index = this.form.value.paths.indexOf(keyword);
            if (index >= 0) {
                this.form.value.paths.splice(index, 1);
            }
        }
    }

    onAddMethod(): void {
        let data = this.methodForm.value.method as string;
        this.form.value.methods?.push(data);
        this.methodForm.reset();
    }

    onRemoveMethod(keyword: any): void {
        if (this.form.value.methods != null) {
            let index = this.form.value.methods.indexOf(keyword);
            if (index >= 0) {
                this.form.value.methods.splice(index, 1);
            }
        }
    }

    onAddFilter(): void {
        let data = this.filterForm.value.filter as RouteFilter;
        this.form.value.filters?.push(data);
        this.filterForm.reset();
    }

    onRemoveFilter(keyword: any): void {
        if (this.form.value.filters != null) {
            let index = this.form.value.filters.indexOf(keyword);
            if (index >= 0) {
                this.form.value.filters.splice(index, 1);
            }
        }
    }

    onAddCacheMethod(): void {
        let data = this.cacheMethodForm.value.cacheMethod as string;
        this.form.value.cache_methods?.push(data);
        this.cacheMethodForm.reset();
    }

    onRemoveCacheMethod(keyword: any): void {
        if (this.form.value.cache_methods != null) {
            let index = this.form.value.cache_methods.indexOf(keyword);
            if (index >= 0) {
                this.form.value.cache_methods.splice(index, 1);
            }
        }
    }

    compareFn(object1: any, object2: any) {
        return object1 && object2 && object1._id === object2._id;
    }

    get f(): { [key: string]: AbstractControl } {
        return this.form.controls;
    }
}