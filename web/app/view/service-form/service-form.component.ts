import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatDialog} from '@angular/material/dialog';
import {CommonModule} from '@angular/common';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatChipsModule} from '@angular/material/chips';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatSortModule} from '@angular/material/sort';
import {MatTabsModule} from '@angular/material/tabs';
import {MatTooltipModule} from '@angular/material/tooltip';
import {TranslateModule} from '@ngx-translate/core';
import {
    ServiceBindFormDialogComponent
} from 'app/components/service-bind-form-dialog/service-bind-form-dialog.component';
import {
    ServiceHeaderFormDialogComponent
} from 'app/components/service-header-form-dialog/service-header-form-dialog.component';
import {
    ServiceRouteFormDialogComponent
} from 'app/components/service-route-form-dialog/service-route-form-dialog.component';
import {Upstream} from 'app/models/upstream';
import {Jail} from 'app/models/jail';
import {Sensor} from 'app/models/sensor';
import {Bind, Header, Route, Service} from 'app/models/service';
import {JailService} from 'app/services/jail.service';
import {ServiceService} from 'app/services/service.service';
import {NotificationService} from 'app/services/notification.service';
import {DragDropModule} from '@angular/cdk/drag-drop';
import {MatExpansionModule} from '@angular/material/expansion';
import {Certificate} from "../../models/certificate";
import {CertificateService} from "../../services/certificate.service";
import {MatStepperModule} from "@angular/material/stepper";
import {OAuthService} from "../../services/oauth.service";
import {FormaterService} from "../../services/formater.service";

@Component({
    selector: 'app-service-form',
    standalone: true,
    imports: [RouterModule, CommonModule, MatExpansionModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule, DragDropModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, MatTabsModule, MatGridListModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule, MatCheckboxModule,
        MatFormFieldModule, MatChipsModule, MatStepperModule],
    templateUrl: './service-form.component.html'
})
export class ServiceFormComponent implements OnInit {

    _certificates: Certificate[];
    _jails: Jail[]

    isAddMode: boolean;
    bindingDS: MatTableDataSource<Bind>;
    bindingDC: string[] = ['port', 'protocol', 'ssl_upgrade', 'action'];

    headerDS: MatTableDataSource<Header>;
    headerDC: string[] = ['name', 'content', 'action'];

    routeDS: MatTableDataSource<Route>;
    routeDC: string[] = ['Name', 'Upstream Target', 'Location Paths', 'action'];

    sansForm = new FormGroup({
        cn: new FormControl<string>('')
    });
    jailForm = new FormGroup({
        jail: new FormControl<Jail>({} as Jail)
    });
    protocolForm = new FormGroup({
        text: new FormControl<string>('')
    });

    form = new FormGroup({
        _id: new FormControl<string>(""),
        name: new FormControl<string>('', {
            validators: [
                Validators.required,
                Validators.minLength(4),
            ]
        }),
        body_limit: new FormControl<number>(10),
        timeout: new FormControl<number>(120),
        bindings: new FormControl<Array<Bind>>([]),
        headers: new FormControl<Array<Header>>([]),
        routes: new FormControl<Array<Route>>([]),
        inspect_level: new FormControl<number>(3),
        inbound_score: new FormControl<number>(15),
        outbound_score: new FormControl<number>(15),
        buffer: new FormControl<number>(256),
        compression: new FormControl<boolean>(true),
        rate_limit: new FormControl<boolean>(true),
        rate_limit_per_sec: new FormControl<number>(256),
        jail_enable: new FormControl<boolean>(false),
        jails: new FormControl<Array<Jail>>([]),
        sans: new FormControl<Array<string>>([]),
        ssl_protocols: new FormControl<Array<string>>(['TLSv1', 'TLSv1.1', 'TLSv1.2', 'TLSv1.3']),
        certificate: new FormControl<Certificate>({} as Certificate),

        ssl_client_auth: new FormControl<boolean>(false),
        ssl_client_ca: new FormControl<string>(''),
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private confirmDialog: MatDialog,
        private notificationService: NotificationService,
        private serviceService: ServiceService,
        private jailService: JailService,
        private certificateService: CertificateService,
        protected oauth: OAuthService,
        protected formater: FormaterService
    ) {
        this.headerDS = new MatTableDataSource<Header>;
        this.routeDS = new MatTableDataSource<Route>;
        this.bindingDS = new MatTableDataSource<Bind>;
        this.isAddMode = false;
        this._jails = [];
        this._certificates = [];
    }

    ngOnInit(): void {
        this.isAddMode = !this.route.snapshot.params['id'];
        if (!this.isAddMode) {
            this.serviceService.getById(this.route.snapshot.params['id'])
                .subscribe(data => {
                    this.form.get('_id')?.setValue(data._id as string);
                    this.form.get('name')?.setValue(data.name);
                    this.form.get('headers')?.setValue(data.headers);
                    this.headerDS.data = data.headers;
                    this.form.get('routes')?.setValue(data.routes);
                    this.routeDS.data = data.routes;
                    this.form.get('bindings')?.setValue(data.bindings);
                    this.bindingDS.data = data.bindings;
                    this.form.get('body_limit')?.setValue(data.body_limit);
                    this.form.get('timeout')?.setValue(data.timeout);
                    this.form.get('inspect_level')?.setValue(data.inspect_level);
                    this.form.get('inbound_score')?.setValue(data.inbound_score);
                    this.form.get('outbound_score')?.setValue(data.outbound_score);
                    this.form.get('buffer')?.setValue(data.buffer);
                    if (data.sans)
                        this.form.get('sans')?.setValue(data.sans);

                    this.form.get('compression')?.setValue(data.compression);
                    this.form.get('rate_limit')?.setValue(data.rate_limit);
                    this.form.get('rate_limit_per_sec')?.setValue(data.rate_limit_per_sec);
                    this.form.get('jail_enable')?.setValue(data.jail_enable);
                    if (data.jails)
                        this.form.get('jails')?.setValue(data.jails);
                    else
                        this.form.get('jails')?.setValue([]);

                    this.form.get('certificate')?.setValue(data.certificate);
                    if (data.ssl_protocols)
                        this.form.get('ssl_protocols')?.setValue(data.ssl_protocols);
                    this.form.get('ssl_client_auth')?.setValue(data.ssl_client_auth);
                    if (data.ssl_client_auth)
                        this.form.get('ssl_client_ca')?.setValue(data.ssl_client_ca);
                });
        } else {
            const basicHeaders = [
                <Header>{name: "X-Powered-By", content: "Tooka"},
                <Header>{name: "X-XSS-Protection", content: "1; mode=block"},
                <Header>{name: "X-Frame-Options", content: "SAMEORIGIN"},
                // <Header>{ name: "Content-Security-Policy", value: "default-src 'self';" }
            ];

            this.form.get('headers')?.setValue(basicHeaders);
            this.headerDS.data = basicHeaders;
        }

        this.certificateService.get().subscribe(data => {
            this._certificates = data.data;
        });
        this.jailService.get().subscribe((data) => {
            this._jails = data.data;
        });
    }

    hasSslSupport() {
        if (this.form.value.bindings)
            for (const binding of this.form.value.bindings) {
                if (binding.protocol == 'HTTPS') {
                    return true;
                }
            }
        return false;
    }


    onAddJail(): void {
        let j = this.jailForm.value.jail as Jail;
        if (this.form.value.jails)
            this.form.value.jails?.push(j);
        this.jailForm.reset();
    }

    onRemoveJail(keyword: any): void {
        if (this.form.value.jails != null) {
            let index = this.form.value.jails.indexOf(keyword);
            if (index >= 0) {
                this.form.value.jails.splice(index, 1);
            }
        }
    }

    onAddCN(): void {
        const formData = this.sansForm.value.cn as string;
        this.form.value.sans?.push(formData);
        this.sansForm.reset();
    }

    onRemoveCN(keyword: any): void {
        if (this.form.value.sans != null) {
            let index = this.form.value.sans.indexOf(keyword);
            if (index >= 0) {
                this.form.value.sans.splice(index, 1);
            }
        }
    }

    moveRoute(event: any) {
        const _data = this.form.value as Service;
        let element = _data.routes[event.previousIndex];
        _data.routes.splice(event.previousIndex, 1);
        _data.routes.splice(event.currentIndex, 0, element);
        this.form.reset(_data);
    }

    onSubmit() {
        if (this.form.status === "INVALID") {
            let errors = [] as Array<string>;
            Object.keys(this.form.controls)
                .forEach(k => {
                    let control = this.form.get(k) as FormControl;
                    if (control.status !== "VALID") {
                        errors.push(" Invalid value on " + k);
                    }
                });
            return;
        }
        let _data: Service = JSON.parse(JSON.stringify(this.form.value));

        if (_data._id === "") {
            Reflect.deleteProperty(_data, '_id');
        }
        if (!_data.jail_enable) {
            Reflect.deleteProperty(_data, 'jail');
        }
        if (!this.hasSslSupport()) {
            Reflect.deleteProperty(_data, 'certificate');
        }

        if (_data.routes)
            for (let i = 0; i < _data.routes.length; i++) {
                _data.routes[i].upstream = <Upstream>{"_id": _data.routes[i].upstream._id};
                if (_data.routes[i].sensor)
                    _data.routes[i].sensor = <Sensor>{"_id": _data.routes[i].sensor._id};
                else
                    Reflect.deleteProperty(_data.routes[i], 'sensor');
            }

        if (this.isAddMode) {
            this.serviceService.save(_data).subscribe((data) => {
                this.router.navigate(['/service']);
                this.notificationService.openSnackBar('Service saved');
            });
        } else {
            this.serviceService.update(_data._id as string, _data).subscribe((data) => {
                this.router.navigate(['/service']);
                this.notificationService.openSnackBar('Service updated');
            });
        }
    }

    onBindRemove(index: number) {
        const data = this.bindingDS.data;
        data.splice(index, 1);
        this.bindingDS.data = data;
    }

    onAddBind() {
        let excludeList = [] as Array<string>;
        for (const b of this.bindingDS.data) {
            excludeList.push(b.protocol);
        }
        const dialogRef = this.confirmDialog.open(ServiceBindFormDialogComponent, {
            width: '450px',
            data: {
                bind: {} as Bind,
                supportedProtocols: ['HTTP', 'HTTPS'].filter(item => !excludeList.includes(item)) as Array<string>
            }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.bindingDS.data;
                data.push(result);
                this.bindingDS.data = data;
                this.form.get('bindings')?.reset(data);
            }
        });
    }

    onEditBind(index: number) {
        const dialogRef = this.confirmDialog.open(ServiceBindFormDialogComponent,
            {
                maxWidth: undefined,
                data: this.bindingDS.data[index]
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.onBindRemove(index);
                const data = this.bindingDS.data;
                data.push(result);
                this.bindingDS.data = data;
                this.form.get('bindings')?.reset(data);
            }
        });
    }

    onRemoveHeader(selectedIndex: number) {
        const data = this.headerDS.data;
        data.splice(selectedIndex, 1);
        this.headerDS.data = data;
    }

    onAddHeader() {
        const dialogRef = this.confirmDialog.open(ServiceHeaderFormDialogComponent, {
            width: '450px',
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.headerDS.data;
                data.push(result);
                this.headerDS.data = data;
                this.form.get('headers')?.reset(data);
            }
        });
    }

    onRemoveRoute(index: number) {
        const data = this.routeDS.data;
        data.splice(index, 1);
        this.routeDS.data = data;
        this.form.get('routes')?.reset(data);
    }

    onAddRoute() {
        const dialogRef = this.confirmDialog.open(ServiceRouteFormDialogComponent,
            {
                maxWidth: undefined
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                const data = this.routeDS.data;
                data.push(result);
                this.routeDS.data = data;
                this.form.get('routes')?.reset(data);
            }
        });
    }

    onEditRoute(index: number) {
        const dialogRef = this.confirmDialog.open(ServiceRouteFormDialogComponent,
            {
                maxWidth: undefined,
                data: this.routeDS.data[index]
            });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.routeDS.data[index] = result;
            }
        });
    }

    onAddProto(): void {

        let data = this.protocolForm.value.text as string;
        this.form.value.ssl_protocols?.push(data);
        console.log(this.form.value.ssl_protocols)

        this.protocolForm.reset();
    }

    onRemoveProto(keyword: any): void {
        if (this.form.enabled)
            if (this.form.value.ssl_protocols != null) {
                let index = this.form.value.ssl_protocols.indexOf(keyword);
                if (index >= 0) {
                    this.form.value.ssl_protocols.splice(index, 1);
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