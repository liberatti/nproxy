import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {MatSlideToggleChange, MatSlideToggleModule} from '@angular/material/slide-toggle';
import {BreakpointObserver} from '@angular/cdk/layout';
import {DefaultPageMeta} from 'app/models/shared';
import {CommonModule} from '@angular/common';
import {ReactiveFormsModule} from '@angular/forms';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSortModule} from '@angular/material/sort';
import {MatTooltipModule} from '@angular/material/tooltip';
import {RouterModule} from '@angular/router';
import {TranslateModule} from '@ngx-translate/core';
import {ConfirmDialogComponent} from 'app/components/confirm-dialog/confirm-dialog.component';
import {Service} from 'app/models/service';
import {ServiceService} from 'app/services/service.service';
import {NotificationService} from 'app/services/notification.service';
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-service-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './service-list.component.html'
})

export class ServiceListComponent implements OnInit {
    serviceDC: string[] = ['name', 'sans', 'routes', 'action'];
    serviceDS: MatTableDataSource<Service>;
    servicePA = new DefaultPageMeta();

    constructor(
        private notificationService: NotificationService,
        private serviceService: ServiceService,
        private confirmDialog: MatDialog,
        private responsive: BreakpointObserver,
        protected oauth: OAuthService,
    ) {
        this.serviceDS = new MatTableDataSource<Service>;
        /**
         * this.responsive.observe([Breakpoints.Small])
         .subscribe(result => {
         if (result.breakpoints[Breakpoints.Small]) {
         this.serviceDC = ['name', 'action'];
         }
         });
         */
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    updateGridTable() {
        this.serviceService.get(this.servicePA).subscribe(data => {
            if (data.metadata) {
                this.serviceDS.data = data.data;
                this.servicePA.total_elements = data.metadata.total_elements;
            } else {
                this.serviceDS.data = [];
                this.servicePA.total_elements = 0;
            }
        });
    }


    onSave() {
        this.serviceService.get(this.servicePA).subscribe(data => {
            this.updateGridTable();
        });
    }

    onRemove(dto: Service) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm service removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            // accepted
            if (result && dto._id) {
                this.serviceService.removeById(dto._id).subscribe(data => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('Service removed');
                });
            }
        });
    }

    nextPage(event: PageEvent) {
        this.servicePA.page = event.pageIndex;
        this.servicePA.per_page = event.pageSize;
        this.updateGridTable();
    }

    toggleServiceActive(i: number, e: MatSlideToggleChange) {
        const service = {
            _id: this.serviceDS.data[i]['_id'],
            active: e.checked
        } as Partial<Service>;

        this.serviceService.patch(service['_id'] as string, service).subscribe(data => {
            this.updateGridTable();
        });
    }
}