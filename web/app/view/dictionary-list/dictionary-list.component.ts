import {Component, OnInit} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {CommonModule} from '@angular/common';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
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
import {Dictionary} from 'app/models/dictionary';
import {DefaultPageMeta} from 'app/models/shared';
import {NotificationService} from 'app/services/notification.service';
import {DictionaryService} from 'app/services/dictionary.service';
import {MatChipsModule} from '@angular/material/chips';
import {MatSlideToggle} from "@angular/material/slide-toggle";
import {OAuthService} from "../../services/oauth.service";


@Component({
    selector: 'app-dictionary-list',
    standalone: true,
    imports: [RouterModule, CommonModule,
        ReactiveFormsModule, TranslateModule,
        MatMomentDateModule,
        MatSidenavModule, MatIconModule, MatButtonModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule,
        MatFormFieldModule, MatChipsModule, MatSlideToggle, FormsModule],
    templateUrl: './dictionary-list.component.html'
})
export class DictionaryListComponent implements OnInit {

    dictionaryDC: string[] = ['name', 'description', 'type', 'action'];
    dictionaryDS: MatTableDataSource<Dictionary>;
    dictionaryPA = new DefaultPageMeta();
    filter: any = {userOnly: true, regex: ""};

    constructor(
        private notificationService: NotificationService,
        private dictService: DictionaryService,
        private confirmDialog: MatDialog,
        protected oauth: OAuthService,
    ) {
        this.dictionaryDS = new MatTableDataSource<Dictionary>;
    }

    ngOnInit(): void {
        this.updateGridTable();
    }

    updateGridTable() {
        this.dictService.search(this.filter, this.dictionaryPA).subscribe(data => {
            if (data.metadata) {
                this.dictionaryDS.data = data.data;
                this.dictionaryPA.total_elements = data.metadata.total_elements;
            } else {
                this.dictionaryDS.data = [];
                this.dictionaryPA.total_elements = 0;
            }
        });
    }

    nextPage(event: PageEvent) {
        this.dictionaryPA.page = event.pageIndex + 1;
        this.dictionaryPA.per_page = event.pageSize;
        this.updateGridTable();
    }

    onRemove(dto: Dictionary) {
        const dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
            data: {title: "Confirm Dictionary removal ", message: "Remove " + dto.name},
        });

        dialogRef.afterClosed().subscribe(result => {
            // accepted
            if (result && dto._id) {
                this.dictService.removeById(dto._id).subscribe(data => {
                    this.updateGridTable();
                    this.notificationService.openSnackBar('Dictionary removed');
                });
            }
        });
    }
}
