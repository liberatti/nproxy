import {HttpErrorResponse, HttpInterceptorFn} from '@angular/common/http';
import {inject, NgZone} from '@angular/core';
import {Router} from '@angular/router';
import {catchError, switchMap, throwError} from 'rxjs';
import {OAuthService} from '../services/oauth.service';
import {APIErrorResponse, OIDCToken} from '../models/shared';
import {NotificationService} from "../services/notification.service";

export const JwtInterceptor: HttpInterceptorFn = (req, next) => {

    const ngZone = inject(NgZone);
    const router = inject(Router);
    const authService = inject(OAuthService);
    const notificationService = inject(NotificationService);

    const accessToken = authService.getAccessToken();
    let authReq = req.clone({
        headers: req.headers
            .set('Authorization', accessToken ? `Bearer ${accessToken}` : '')
    });
    if (!req.headers.has('Content-Type')) {
        if (req.body instanceof FormData) {
            authReq = authReq.clone({
                headers: authReq.headers
                    //.set('Content-Type', 'multipart/form-data')
                    .set('Pragma', 'no-cache')
            });
        } else {
            authReq = authReq.clone({
                headers: authReq.headers
                    .set('Content-Type', 'application/json')
                    .set('Pragma', 'no-cache')
            });
        }
    }

    function isAPIErrorResponse(error: any): error is APIErrorResponse {
        return (
            typeof error.error.code === 'number' &&
            typeof error.error.message === 'string' &&
            typeof error.error.method === 'string' &&
            typeof error.error.url === 'string'
        );
    }

    //console.log('Requisição HTTP:', req);
    //console.log('Cabeçalhos:', req.headers);
    //if (req.body instanceof FormData)
    //    (req.body as FormData).forEach((v, k) => {
    //        console.log(`Key: ${k}, Value: ${v}`);
    //    });
    return next(authReq).pipe(
        catchError((err: any) => {
            if (err instanceof HttpErrorResponse) {
                if (err.status === 401) {
                    try {
                        return authService.refreshToken().pipe(
                            switchMap((newTokens: OIDCToken) => {
                                authService.storeTokens(newTokens);
                                const clonedRequest = req.clone({
                                    setHeaders: {
                                        Authorization: `Bearer ${newTokens.access_token}`
                                    }
                                });
                                return next(clonedRequest);
                            }),
                            catchError((refreshError) => {
                                ngZone.run(() => {
                                    router.navigateByUrl('/signin');
                                });
                                return throwError(() => new Error('Token refresh failed'));
                            })
                        );
                    } catch (e) {
                        router.navigateByUrl('/signin');
                        return throwError(() => err);
                    }
                } else {
                    if (isAPIErrorResponse(err)) {
                        notificationService.openSnackBar('[' + err.error.code + '] ' + err.error.message);
                    } else {
                        console.error('Unknown error:', {status: err.status, message: err.message});
                    }
                }
            } else {
                console.error('An error occurred:', err);
            }
            return throwError(() => err);
        })
    );
};
