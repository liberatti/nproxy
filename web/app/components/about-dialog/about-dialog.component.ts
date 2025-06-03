import {Component} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatDialogActions, MatDialogContent, MatDialogRef} from '@angular/material/dialog';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {ClusterService} from 'app/services/cluster.service';
import {saveAs} from 'file-saver';
import {HttpClient} from '@angular/common/http';
import {MatTabChangeEvent, MatTabsModule} from '@angular/material/tabs';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';
import {TranslateModule} from '@ngx-translate/core';
import {RouterModule} from '@angular/router';
import {NotificationService} from "../../services/notification.service";
import { environment } from 'environments/environment';


@Component({
    selector: 'app-about-dialog',
    templateUrl: './about-dialog.component.html',
    styleUrl: './about-dialog.component.css',
    standalone: true,
    imports: [
        CommonModule, RouterModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogContent,
        MatDialogActions,
        MatTabsModule, MatIconModule, TranslateModule
    ],
})

export class AboutDialogComponent {
    selectedFile: File | null = null;
    currentTab: number = 0;
    restoreReady: boolean = true;
    _REST_API_URL: string = environment.apiUrl;
    constructor(
        public dialogRef: MatDialogRef<AboutDialogComponent>,
        private clusterService: ClusterService, private http: HttpClient,
        private notificationService: NotificationService,
    ) {
    }

    onFileSelected(event: any): void {
        this.selectedFile = event.target.files[0];
        if (this.selectedFile && this.selectedFile.type !== 'application/zip') {
            this.notificationService.openSnackBar('Only ZIP files are allowed');
            this.selectedFile = null;
        }
    }

    onSubmit(): void {
        if (!this.selectedFile) {
            this.notificationService.openSnackBar('Please select a ZIP file to upload');
            return;
        }
        let formData = new FormData();
        formData.append('zipfile', this.selectedFile, this.selectedFile.name);
        this.restoreReady = false;

        this.clusterService.uploadConfig(formData).subscribe({
            next: (data) => {
                this.restoreReady = true;
                this.dialogRef.close(false);
            },
            error: (err) => {
                this.restoreReady = true;
                this.notificationService.openSnackBar('Failed to restore');
            }
        });
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }

    downloadConfig(): void {
        this.clusterService.downloadConfig().subscribe((resultBlob) => {
            const blob = new Blob([resultBlob], {type: 'application/zip'});
            saveAs(blob, 'config.zip');
        });
    }

    onTabChanged(event: MatTabChangeEvent) {
        this.currentTab = event.index;
    }
}