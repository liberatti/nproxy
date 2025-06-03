import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {CommonModule} from '@angular/common';
import {ReactiveFormsModule} from '@angular/forms';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
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
import {DefaultPageMeta} from 'app/models/shared';
import {NotificationService} from 'app/services/notification.service';
import {MatChipsModule} from '@angular/material/chips';
import {RouteFilter} from "../../models/service";
import {RoutefilterService} from "../../services/routefilter.service";
import {OAuthService} from "../../services/oauth.service";


@Component({
    selector: 'app-route_filter-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './route_filter-list.component.html'
})
export class RouteFilterListComponent implements OnInit {

    route_filterDC: string[] = ['name', 'description', 'type', 'action'];
    route_filterDS: MatTableDataSource<RouteFilter>;
    route_filterPA = new DefaultPageMeta();

    constructor(
        private notificationService: NotificationService,
        private dictService: RoutefilterService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.route_filterDS = new MatTableDataSource<RouteFilter>;
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    updateGridTable() {
        this.dictService.get(this.route_filterPA).subscribe(data => {
            this.route_filterDS.data = data.data;
            if (data.metadata)
                this.route_filterPA.total_elements = data.metadata.total_elements;
        });
    }

    nextPage(event: PageEvent) {
        this.route_filterPA.page = event.pageIndex + 1;
        this.route_filterPA.per_page = event.pageSize;
        this.updateGridTable();
    }

    onRemove(dto: RouteFilter) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm route_filter removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            // accepted
            if (result && dto._id) {
                this.dictService.removeById(dto._id).subscribe(data => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('route_filter removed');
                });
            }
        });
    }
}
