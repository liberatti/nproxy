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
import {User} from "../../models/oauth";
import {OAuthService, UserService} from "../../services/oauth.service";


@Component({
    selector: 'app-user-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule],
    templateUrl: './user-list.component.html'
})
export class UserListComponent implements OnInit {

    userDC: string[] = ['name', 'email', 'role', 'action'];
    userDS: MatTableDataSource<User>;
    userPA = new DefaultPageMeta();

    constructor(
        private notificationService: NotificationService,
        private dictService: UserService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.userDS = new MatTableDataSource<User>;
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    updateGridTable() {
        this.dictService.get(this.userPA).subscribe(data => {
            this.userDS.data = data.data;
            this.userPA.total_elements = data.metadata.total_elements;
        });
    }

    nextPage(event: PageEvent) {
        this.userPA.page = event.pageIndex + 1;
        this.userPA.per_page = event.pageSize;
        this.updateGridTable();
    }

    onRemove(dto: User) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm user removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            // accepted
            if (result && dto._id) {
                this.dictService.removeById(dto._id).subscribe(data => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('user removed');
                });
            }
        });
    }
}
