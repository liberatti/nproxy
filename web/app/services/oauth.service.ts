import {Injectable, Injector} from '@angular/core';
import {APIService} from './api.service';
import {Observable} from 'rxjs';
import {HttpHeaders, HttpParams} from '@angular/common/http';
import {Router} from '@angular/router';
import moment from 'moment';
import {jwtDecode} from 'jwt-decode';
import {User} from '../models/oauth';
import {LocalStorageService} from './localstorage.service';
import {OIDCToken} from '../models/shared';

@Injectable({
    providedIn: 'root'
})
export class UserService extends APIService<User, string> {

    constructor(
        protected override injector: Injector
    ) {
        super(injector, 'user')
    }

    updateAccount(_id: string, data: User): Observable<OIDCToken> {
        return this.httpClient.put<OIDCToken>(this.END_POINT + `/${_id}/account`, data);
    }
}


@Injectable({
    providedIn: 'root'
})
export class OAuthService extends APIService<OIDCToken, string> {

    userInfoData: any = null;

    constructor(
        protected override injector: Injector,
        private localStorage: LocalStorageService,
        private router: Router
    ) {
        super(injector, 'oauth')
    }

    storeTokens(token: OIDCToken) {
        const payload = jwtDecode(token.access_token) as OIDCToken;
        this.localStorage.set('oidc', Object.assign({}, token, {
            'created_on': moment().toISOString(),
            'role': payload.profile.role
        }));
    }


    resetTokens() {
        this.localStorage.remove('oidc')
    }

    getAccessToken() {
        const oidc = this.localStorage.get('oidc') as OIDCToken;
        if (oidc)
            return oidc.access_token;
        else
            return null;
    }

    refreshToken(): Observable<OIDCToken> {
        const oidc = this.localStorage.get('oidc') as OIDCToken;
        if (!oidc) {
            this.router.navigate(['/sigin']);
        }

        const headers = new HttpHeaders({
            'Refresh-Token': oidc['refresh_token'],
        });
        return this.httpClient.get<OIDCToken>(`${this.END_POINT}/token`, {headers});
    }

    authorizeCode(provider: String, code: String): Observable<OIDCToken> {
        let params = new HttpParams();
        params = params.append('code', `${code}`);
        return this.httpClient.get<any>(this.END_POINT + `/${provider}/callback`, {params: params});
    }

    isRole(role: string) {
        const ui = this.userInfo();
        if (ui) {
            return ui.role == role;
        }
        return false;
    }

    userInfo(): User | undefined {
        if (!this.userInfoData) {
            const oidc = this.localStorage.get('oidc') as OIDCToken;
            if (!oidc) {
                this.router.navigate(['/sigin']);
            }

            try {
                const u = jwtDecode(oidc.access_token) as OIDCToken
                this.userInfoData = u.profile;
                return this.userInfoData;
            } catch (error) {
                this.router.navigate(['/signin']);
            }
        } else {
            return this.userInfoData;
        }
        return undefined;
    }

    login(data: User): Observable<OIDCToken> {
        return this.httpClient.post<OIDCToken>(this.END_POINT + "/login", data);
    }

    logout(): Observable<OIDCToken> {
        return this.httpClient.delete<OIDCToken>(this.END_POINT + "/logout");
    }
}