import {Routes} from '@angular/router';
import {AdminLayoutComponent} from './layouts/admin-layout/admin-layout.component';
import {SignInComponent} from './view/sign-in/sign-in.component';
import {PublicLayoutComponent} from './layouts/public-layout/public-layout.component';
import {CertificateListComponent} from './view/certificate-list/certificate-list.component';
import {CertificateFormComponent} from './view/certificate-form/certificate-form.component';
import {UpstreamListComponent} from './view/upstream-list/upstream-list.component';
import {UpstreamFormComponent} from './view/upstream-form/upstream-form.component';
import {SensorListComponent} from './view/sensor-list/sensor-list.component';
import {SensorFormComponent} from './view/sensor-form/sensor-form.component';
import {ServiceListComponent} from './view/service-list/service-list.component';
import {ServiceFormComponent} from './view/service-form/service-form.component';
import {AccountComponent} from './view/account-form/account-form.component';
import {TransactionListComponent} from './view/transaction-list/transaction-list.component';
import {JailListComponent} from './view/jail-list/jail-list.component';
import {JailFormComponent} from './view/jail-form/jail-form.component';
import {ConfigFormComponent} from './view/config-form/config-form.component';
import {FeedListComponent} from "./view/feed-list/feed-list.component";
import {FeedFormComponent} from "./view/feed-form/feed-form.component";
import {DashboardHomeComponent} from "./view/dashboard-home/dashboard-home.component";
import {RouteFilterListComponent} from "./view/route_filter-list/route_filter-list.component";
import {RouteFilterFormComponent} from "./view/route_filter-form/route_filter-form.component";
import {UserListComponent} from "./view/user-list/user-list.component";
import {UserFormComponent} from "./view/user-form/user-form.component";

export const routes: Routes = [
    {
        path: 'dashboard',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: DashboardHomeComponent},
        ]
    },
    {
        path: 'trn',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: TransactionListComponent}
        ]
    },
    {
        path: 'service',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: ServiceListComponent},
            {path: 'add', component: ServiceFormComponent},
            {path: 'edit/:id', component: ServiceFormComponent},
        ]
    },
    {
        path: 'feed',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: FeedListComponent},
            {path: 'add', component: FeedFormComponent},
            {path: 'edit/:id', component: FeedFormComponent},
        ]
    },
    {
        path: 'users',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: UserListComponent},
            {path: 'add', component: UserFormComponent},
            {path: 'edit/:id', component: UserFormComponent},
        ]
    },
    {
        path: 'route_filter',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: RouteFilterListComponent},
            {path: 'add', component: RouteFilterFormComponent},
            {path: 'edit/:id', component: RouteFilterFormComponent},
        ]
    },
    {
        path: 'jail',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: JailListComponent},
            {path: 'add', component: JailFormComponent},
            {path: 'edit/:id', component: JailFormComponent},
        ]
    },
    {
        path: 'ups',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: UpstreamListComponent},
            {path: 'add', component: UpstreamFormComponent},
            {path: 'edit/:id', component: UpstreamFormComponent},
        ]
    },
    {
        path: 'sensor',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: SensorListComponent},
            {path: 'add', component: SensorFormComponent},
            {path: 'edit/:id', component: SensorFormComponent},
        ]
    },
    {
        path: 'certificate',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: CertificateListComponent},
            {path: 'add', component: CertificateFormComponent},
            {path: 'edit/:id', component: CertificateFormComponent},
        ]
    },
    {
        path: 'account',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: AccountComponent},
        ]
    },
    {
        path: 'signin',
        component: PublicLayoutComponent,
        children: [
            {path: '', component: SignInComponent},
        ]
    },
    {
        path: 'config',
        component: AdminLayoutComponent,
        children: [
            {path: '', component: ConfigFormComponent},
        ]
    },
    {
        path: '**',
        redirectTo: 'dashboard',
        pathMatch: 'full'
    }
];