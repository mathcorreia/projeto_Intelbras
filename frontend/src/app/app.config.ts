import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';

// 1. Importe o provideHttpClient e o withFetch
import { provideHttpClient, withFetch } from '@angular/common/http';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // 2. Adicione o provedor aqui
    provideHttpClient(withFetch()) 
  ]
};