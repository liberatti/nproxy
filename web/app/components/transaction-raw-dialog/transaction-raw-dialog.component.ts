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
import {TransactionLog} from 'app/models/transaction';
import { HighlightModule } from 'ngx-highlightjs';

@Component({
    selector: 'app-atransaction-raw-dialog',
    templateUrl: './transaction-raw-dialog.component.html',
    standalone: true,
    imports: [
        CommonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule, MatCardModule,
        MatButtonModule,
        MatDialogTitle,
        MatDialogContent,
        MatDialogActions,
        MatTabsModule, MatIconModule,
        HighlightModule
    ]
})

export class TransactionRAWDialogComponent {
    constructor(
        @Inject(MAT_DIALOG_DATA) public data: TransactionLog,
        public dialogRef: MatDialogRef<TransactionRAWDialogComponent>
    ) { }

    get jsonData(): string {
        return JSON.stringify(this.data, null, 4);
    }

    onDismiss(): void {
        this.dialogRef.close(false);
    }
}