import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, Injector } from '@angular/core';
import {  Observable } from 'rxjs';
import { APIOperations, Page, PageMeta } from '../models/shared';
import { REST_API_URL } from '../app.config';

@Injectable({
    providedIn: 'root'
})
export abstract class APIService<T, ID> implements APIOperations<T, ID> {
    protected readonly END_POINT: string;
    protected httpClient: HttpClient;

    protected constructor(
        protected injector: Injector,
        protected ctx: string
    ) {
        const _REST_API_URL = injector.get(REST_API_URL)
        this.httpClient = this.injector.get(HttpClient)
        this.END_POINT = `${_REST_API_URL}/api/${ctx}`;
    }

    get(pagination?: PageMeta): Observable<Page> {
        let params = new HttpParams();
        if (pagination) {
            params = params.append('page', pagination.page);
            params = params.append('size', pagination.per_page);
        }
        return this.httpClient.get<Page>(this.END_POINT, { params: params });
    }

    getById(id: ID): Observable<T> {
        return this.httpClient.get<T>(this.END_POINT + "/" + id);
    }

    getByName(name: string, pagination?: PageMeta): Observable<Page> {
        let options = {
            params: new HttpParams()
        }
        options.params = options.params.append("name", name);
        if (pagination) {
            options.params = options.params.append("page", pagination.page);
            options.params = options.params.append("size", pagination.per_page);
        }
        return this.httpClient.get<Page>(this.END_POINT, options);
    }

    removeById(id: ID): Observable<T> {
        return this.httpClient.delete<T>(this.END_POINT + "/" + id);
    }

    save(data: Partial<T>): Observable<T> {
        return this.httpClient.post<T>(this.END_POINT, data);
    }
    update(id: ID, data: Partial<T>): Observable<T> {
        return this.httpClient.put<T>(this.END_POINT + "/" + id, data);
    }

    patch(id: ID, data: Partial<T>): Observable<T> {
        return this.httpClient.patch<T>(this.END_POINT + "/" + id, data);
    }
}