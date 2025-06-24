import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MAT_SNACK_BAR_DATA, MatSnackBarRef } from '@angular/material/snack-bar';

@Component({
    selector: 'app-multi-snackbar',
    standalone: true,
    imports: [CommonModule],
    template: `
        <div class="multi-snackbar" *ngIf="data && data.messages">
            <div *ngFor="let message of data.messages" class="snackbar-item">
                {{ message }}
            </div>
        </div>
    `,
    styles: [`
        .multi-snackbar {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 8px;
        }
        .snackbar-item {
            padding: 6px;
        }
    `]
})
export class MultiSnackbarComponent {
    constructor(
        public snackBarRef: MatSnackBarRef<MultiSnackbarComponent>,
        @Inject(MAT_SNACK_BAR_DATA) public data: { messages: string[] }
    ) {
        console.log('MultiSnackbarComponent data:', data);
    }
} 