import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MultiSnackbarComponent } from '../components/multi-snackbar/multi-snackbar.component';

@Injectable({
    providedIn: 'root'
})
export class NotificationService {

    constructor(private snackBar: MatSnackBar) { }

    public openSnackBar(message: string | string[]) {
        if (Array.isArray(message)) {
            this.snackBar.openFromComponent(MultiSnackbarComponent, {
                data: { messages: message },
                duration: 5000,
                panelClass: 'snackbar-error',
                verticalPosition: 'bottom',
                horizontalPosition: 'center'
            });
        } else {
            this.snackBar.open(message, '', {
                duration: 5000,
                panelClass: 'snackbar-error',
                verticalPosition: 'bottom',
                horizontalPosition: 'center'
            });
        }
    }
}
