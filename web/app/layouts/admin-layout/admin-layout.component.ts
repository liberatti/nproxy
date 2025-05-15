import {BreakpointObserver, Breakpoints} from '@angular/cdk/layout';
import {AfterViewInit, ChangeDetectorRef, Component, Injector, OnDestroy, OnInit} from '@angular/core';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatToolbarModule} from '@angular/material/toolbar';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {TranslateModule, TranslateService} from '@ngx-translate/core';
import * as moment from 'moment';
import {Subject, takeUntil} from 'rxjs';
import {FrontendConfig, MenuLink} from 'app/models/shared';
import {LocalStorageService} from 'app/services/localstorage.service';
import {MatDialog, MatDialogRef} from '@angular/material/dialog';
import {AboutDialogComponent} from 'app/components/about-dialog/about-dialog.component';
import {ApplyDialogComponent} from 'app/components/apply-dialog/apply-dialog.component';
import {ClusterService} from 'app/services/cluster.service';
import {MatBadgeModule} from '@angular/material/badge';
import {CommonModule} from '@angular/common';
import {MatCardModule} from '@angular/material/card';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {OAuthService} from 'app/services/oauth.service';
import {io} from 'socket.io-client';
import {REST_API_URL} from 'app/app.config';
import {MatChipsModule} from '@angular/material/chips';
import {MatTooltip} from "@angular/material/tooltip";
import {HttpClient} from "@angular/common/http";
import {environment} from 'environments/environment';

@Component({
    selector: 'app-admin-layout',
    standalone: true,
    imports: [RouterModule, CommonModule, TranslateModule, MatProgressBarModule,
        MatSidenavModule, MatIconModule, MatToolbarModule, MatCardModule, MatChipsModule,
        MatButtonModule, MatListModule, MatMenuModule, MatBadgeModule, MatTooltip
    ],
    templateUrl: './admin-layout.component.html',
    styleUrl: './admin-layout.component.css'
})
export class AdminLayoutComponent implements OnInit, AfterViewInit, OnDestroy {

    title: string = environment.name;
    version: string = environment.version;
    config: FrontendConfig = <FrontendConfig>{locale: {key: 'en_US'}, navResource: "transaction", sidenavOpened: false};
    destroyed = new Subject<void>();
    currentScreenSize: string = "";
    updatePending: boolean = false;


    displayNameMap = new Map([
        [Breakpoints.XSmall, 'XSmall'],
        [Breakpoints.Small, 'Small'],
        [Breakpoints.Medium, 'Medium'],
        [Breakpoints.Large, 'Large'],
        [Breakpoints.XLarge, 'XLarge'],
    ]);
    protected httpClient: HttpClient
    menu: Array<MenuLink> = [];
    changes: Array<string> = []
    socket: any;
    trackingEvt: boolean = false;
    applyDialogRef: MatDialogRef<ApplyDialogComponent> | null = null;
    constructor(
        private changeDetectorRef: ChangeDetectorRef,
        protected oauth: OAuthService,
        private localStorage: LocalStorageService,
        private breakpointObserver: BreakpointObserver,
        private translate: TranslateService,
        private portDialog: MatDialog,
        private applyDialog: MatDialog,
        private clusterService: ClusterService,
        protected injector: Injector,
        private route: ActivatedRoute,
        private router: Router
    ) {
        this.httpClient = this.injector.get(HttpClient)
        breakpointObserver
            .observe([
                Breakpoints.XSmall,
                Breakpoints.Small,
                Breakpoints.Medium,
                Breakpoints.Large,
                Breakpoints.XLarge,
            ])
            .pipe(takeUntil(this.destroyed))
            .subscribe(result => {
                for (const query of Object.keys(result.breakpoints)) {
                    if (result.breakpoints[query]) {
                        this.currentScreenSize = this.displayNameMap.get(query) ?? 'Unknown';
                    }
                }
            });
        this.config = this.localStorage.get('ui_config');
    }

    signOut() {
        this.oauth.resetTokens();
        this.router.navigate(['/signin']);
    }


    isMobile() {
        return ['XSmall', 'Small'].includes(this.currentScreenSize);
    }

    isSidenavActive() {
        return this.config && this.config.sidenavOpened;
    }

    toggleSubMenu(link: MenuLink | undefined) {
        if (!link) {
            const currentRoute = this.route.snapshot.url[0]?.path;
            if (!currentRoute) return;
            for (const m of this.menu) {
                if (m.menu && Array.isArray(m.menu)) {
                    for (const sm of m.menu) {
                        if (sm.route?.includes(currentRoute)) {
                            m.expanded = !m.expanded;
                            break;
                        }
                    }
                }
            }
        } else {
            link.expanded = !link.expanded;
        }
    }

    onSidenavToggle() {
        window.dispatchEvent(new Event('resize'));
        if (this.config) {
            this.config.sidenavOpened = !this.config.sidenavOpened;
            this.localStorage.set('ui_config', this.config)
        }
    }
    healthCheck() {
        this.clusterService.healthCheck().subscribe(data => {
            if (data.apply_pendding) {
                this.changes = data.apply_pendding;
                if (this.changes && this.changes.length > 0) {
                    this.trackingEvt = true;
                }
            }
        });
    }

    ngOnInit(): void {
        this.translate.setDefaultLang('en_US');
        this.httpClient.get<any>("assets/main.menu.json").subscribe(data => {
            this.menu = data;
            this.toggleSubMenu(undefined);
        });
        this.healthCheck();
    }

    showAbout() {
        this.portDialog.open(AboutDialogComponent, {
            width: '450px'
        });
    }

    onApply() {
        this.applyDialogRef = this.applyDialog.open(ApplyDialogComponent, {
            width: '450px',
            disableClose: true
        });
    }

    ngAfterViewInit(): void {
        if (this.localStorage.exists('ui_config')) {
            this.config = this.localStorage.get('ui_config');
        } else {
            this.config = {
                locale: 'en_US',
                navResource: 'dashboard',
                sidenavOpened: true,
                display: {
                    "datetime": "YYYY-MM-DDTHH:mm:ss"
                }
            } as FrontendConfig;
            this.localStorage.set('ui_config', this.config);
        }
        this.translate.use(this.config.locale);
        moment.locale(this.config.locale);

        this.changeDetectorRef.detectChanges();
        this.socket = io(this.injector.get(REST_API_URL), {
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 10000,
            reconnectionDelayMax: 20000,
            timeout: 10000,
        });
        this.socket.on('tracking_evt', () => {
            this.trackingEvt = true;
        });
        this.socket.on('tracking_aply', () => {
            this.trackingEvt = false;
            this.applyDialogRef?.close();
        });
        this.clusterService.healthCheck().subscribe(data => {
                this.changes = data.apply_pendding;
                if (this.changes && this.changes.length > 0) {
                    this.trackingEvt = true;
                }
                if (data.apply_active) {
                    this.onApply();
                }
        });
    }

    ngOnDestroy() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}