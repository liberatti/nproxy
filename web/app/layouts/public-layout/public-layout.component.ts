import {ChangeDetectorRef, Component, Injector} from '@angular/core';
import {ActivatedRoute, Router, RouterModule} from '@angular/router';
import {FrontendConfig} from "../../models/shared";
import * as moment from "moment/moment";
import {io} from "socket.io-client";
import {REST_API_URL} from "../../app.config";
import {OAuthService} from "../../services/oauth.service";
import {LocalStorageService} from "../../services/localstorage.service";
import {BreakpointObserver, Breakpoints} from "@angular/cdk/layout";
import {TranslateService} from "@ngx-translate/core";
import {MatDialog} from "@angular/material/dialog";
import {ClusterService} from "../../services/cluster.service";
import {HttpClient} from "@angular/common/http";
import {takeUntil} from "rxjs";

@Component({
  selector: 'app-public-layout',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './public-layout.component.html'
})
export class PublicLayoutComponent {
  config: FrontendConfig = <FrontendConfig>{ locale: { key: 'en_US' }, navResource: "transaction", sidenavOpened: false };

  constructor(
      private localStorage: LocalStorageService,
      private translate: TranslateService,
      protected injector: Injector,
  ) {
    this.config = this.localStorage.get('ui_config');
  }
  ngAfterViewInit(): void {
    if (this.localStorage.exists('ui_config')) {
      this.config = this.localStorage.get('ui_config');
    }else{
      this.config = {
        locale: 'en_US',
        navResource: 'dashboard',
        sidenavOpened: true,
        display:{
          "datetime": "YYYY-MM-DDTHH:mm:ss"
        }
      } as FrontendConfig;
      this.localStorage.set('ui_config',this.config);
    }
    this.translate.use(this.config.locale);
    moment.locale(this.config.locale);
  }
}
