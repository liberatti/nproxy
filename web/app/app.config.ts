import { ApplicationConfig, importProvidersFrom, InjectionToken } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HttpClient, provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { TranslateModule, TranslateLoader } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { JwtInterceptor } from './interceptors/jwt.interceptor';
import { environment } from 'environments/environment';
import { provideMomentDateAdapter} from "@angular/material-moment-adapter";
import { provideHighlightOptions } from 'ngx-highlightjs';

export const REST_API_URL = new InjectionToken<string>('REST_API_URL');
export const API_DATA_FORMAT = new InjectionToken<string>('API_DATA_FORMAT');

export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideHighlightOptions({
      coreLibraryLoader: () => import('highlight.js/lib/core'),
      lineNumbersLoader: () => import('ngx-highlightjs/line-numbers'), // Optional, add line numbers if needed
      languages: {
        json: () => import('highlight.js/lib/languages/json')
      }
    }),
    provideMomentDateAdapter(undefined, {useUtc: true}),
    { provide: REST_API_URL, useValue: environment.apiUrl },
    { provide: API_DATA_FORMAT, useValue: environment.apiDateFormat},
    provideRouter(routes),
    provideAnimationsAsync(),
    provideHttpClient(
      withFetch(), withInterceptors([JwtInterceptor])
    ),
    importProvidersFrom(TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient]
      }
    }))]
};
