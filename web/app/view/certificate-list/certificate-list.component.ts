import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {TranslateModule, TranslateService} from '@ngx-translate/core';
import moment from 'moment';
import {DefaultPageMeta, PageMeta} from 'app/models/shared';
import {ConfirmDialogComponent} from 'app/components/confirm-dialog/confirm-dialog.component';
import {Certificate} from 'app/models/certificate';
import {CertificateService} from 'app/services/certificate.service';
import {NotificationService} from 'app/services/notification.service';
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
import {OAuthService} from "../../services/oauth.service";

@Component({
    selector: 'app-certificate-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './certificate-list.component.html'
})

export class CertificateListComponent implements OnInit {

    certificateDC: string[] = ['status', 'name', 'provider', 'subjects', 'action'];
    certificateDS: MatTableDataSource<Certificate>;
    certificatePA: PageMeta;

    constructor(
        private notificationService: NotificationService,
        private certificateService: CertificateService,
        private confirmDialog: MatDialog,
        private translateService: TranslateService,
        protected oauth: OAuthService,
    ) {
        this.certificateDS = new MatTableDataSource<Certificate>;
        this.certificatePA = new DefaultPageMeta()
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    updateGridTable() {
        this.certificateService.get(this.certificatePA).subscribe(data => {
            if (data.metadata) {
                this.certificateDS.data = data.data;
                this.certificatePA.total_elements = data.metadata.total_elements;
            } else {
                this.certificateDS.data = [];
                this.certificatePA.total_elements = 0;
            }
        });
    }

    nextPage(event: PageEvent) {
        this.certificatePA.page = event.pageIndex + 1;
        this.certificatePA.per_page = event.pageSize;
        this.updateGridTable();
    }

    onSave() {
        this.certificateService.get(this.certificatePA).subscribe(data => {
            this.certificateDS.data = data.data;
            this.certificatePA.total_elements = data.metadata.total_elements;
        });
    }

    onRemove(dto: Certificate) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm Certificate removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            // accepted
            if (result && dto._id) {
                this.certificateService.removeById(dto._id).subscribe(data => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('Certificate removed');
                });
            }
        });
    }

    getStatusTip(e: Certificate) {
        let format = this.translateService.instant('format.display.datetime');
        return `not_after: ${moment(e.not_after).format(format)}
        not_before: ${moment(e.not_before).format(format)}`
    }

    onCertificateRenew(hostname_id: string) {
        this.certificateService.getById(hostname_id).subscribe(data => {
            let h = data as Certificate;
            let ph = {
                _id: h._id,
                force_renew: true
            } as Certificate;
            this.certificateService.patch(hostname_id, ph).subscribe(data => {
            });
        });
    }
}
