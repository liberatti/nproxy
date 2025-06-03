import {Component} from '@angular/core';
import {HashLocationStrategy, LocationStrategy} from '@angular/common';
import {RouterOutlet} from '@angular/router';
import {LocalStorageService} from './services/localstorage.service';
import {NotificationService} from './services/notification.service';
import {FilterByPropertyPipe} from './pipes/filter_by_property.pipe';
import {CertificateService} from './services/certificate.service';
import {UpstreamService} from './services/upstream.service';
import {ServiceService} from './services/service.service';
import {SensorService} from './services/sensor.service';
import {ByteFormatPipe} from './pipes/format_bytes.pipe';
import {FormaterService} from './services/formater.service';
import {DateFormatPipe} from './pipes/date_format.pipe';
import {OAuthService} from './services/oauth.service';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [RouterOutlet],
    template: '<router-outlet></router-outlet>',
    providers: [
        {provide: LocationStrategy, useClass: HashLocationStrategy},
        {provide: 'LOCALSTORAGE', useValue: window.localStorage},
        FilterByPropertyPipe, ByteFormatPipe, DateFormatPipe,
        OAuthService, NotificationService, LocalStorageService,
        FormaterService,
        CertificateService, UpstreamService, ServiceService,
        SensorService, NotificationService
    ],
})
export class AppComponent {


}