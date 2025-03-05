import {Component, Inject} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle
} from '@angular/material/dialog';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatTabsModule} from '@angular/material/tabs';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';
import {TranslateModule} from '@ngx-translate/core';
import {RouterModule} from '@angular/router';
import {NodeStatus, UpstreamStatus} from "../../models/upstream";
import {MatExpansionModule} from "@angular/material/expansion";


@Component({
    selector: 'app-node-details-dialog',
    templateUrl: './node-details-dialog.component.html',
    standalone: true,
    imports: [
        CommonModule, RouterModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogContent,
        MatDialogActions,
        MatTabsModule, MatIconModule, TranslateModule, MatExpansionModule, MatDialogTitle
    ],
})

export class NodeDetailsDialogComponent {

    constructor(
        public dialogRef: MatDialogRef<any>,
        @Inject(MAT_DIALOG_DATA) public data: NodeStatus
    ) {
    }

    isHealthy(ups: UpstreamStatus): boolean {
        for (const up of ups.targets) {
            if (!up.healthy)
                return false;
        }
        return true;
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }
}