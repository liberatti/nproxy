import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
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
import {Upstream} from 'app/models/upstream';
import {UpstreamService} from 'app/services/upstream.service';
import {NotificationService} from 'app/services/notification.service';
import {DefaultPageMeta} from 'app/models/shared';
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-upstream-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './upstream-list.component.html'
})
export class UpstreamListComponent implements OnInit {
    upstreamDC: string[] = ['name', 'protocol', 'description', 'targetCount', 'action'];
    upstreamDS: MatTableDataSource<Upstream>;
    upstreamPA = new DefaultPageMeta();

    constructor(
        private notificationService: NotificationService,
        private upstreamService: UpstreamService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.upstreamDS = new MatTableDataSource<Upstream>;
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    updateGridTable() {
        this.upstreamService.get(this.upstreamPA).subscribe(data => {
            if (data.metadata) {
                this.upstreamDS.data = data.data;
                this.upstreamPA.total_elements = data.metadata.total_elements;
            } else {
                this.upstreamDS.data = [];
                this.upstreamPA.total_elements = 0;
            }
        });
    }

    nextPage(event: PageEvent) {
        this.upstreamPA.page = event.pageIndex + 1;
        this.upstreamPA.per_page = event.pageSize;
        this.updateGridTable();
    }

    onRemove(dto: Upstream) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm upstream removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result && dto._id) {
                this.upstreamService.removeById(dto._id).subscribe(data => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('Upstream removed');
                });
            }
        });
    }
}
