import {CommonModule} from '@angular/common';
import {Component, OnInit} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {
    MatDialogModule,
    MatDialogRef
} from '@angular/material/dialog';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {ClusterService} from 'app/services/cluster.service';
import {TranslateModule} from "@ngx-translate/core";

@Component({
    selector: 'app-apply-dialog',
    templateUrl: './apply-dialog.component.html',
    standalone: true,
    imports: [
        CommonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogModule,
        MatChipsModule,
        MatIconModule,
        TranslateModule
    ],
})

export class ApplyDialogComponent implements OnInit {
    error: string = "";
    applyReady: boolean = false;
    success: boolean = false;

    constructor(
        public dialogRef: MatDialogRef<ApplyDialogComponent>,
        private clusterService: ClusterService
    ) {

    }

    ngOnInit(): void {
        this.clusterService.healthCheck().subscribe(data => {
            this.applyReady = !data.apply_active;
            if (this.applyReady) {
                this.applyReady = false;
                this.clusterService.applyConfig().subscribe({
                    next: (data) => {
                        this.applyReady = true;
                        this.success = true;
                    },
                    error: (err) => {
                        this.applyReady = true;
                        this.success = false;
                        this.error = err.message || 'An error occurred during configuration';
                    }
                });
            }
        });

    }

    closeDialog() {
        this.dialogRef.close(this.success);
    }
}
