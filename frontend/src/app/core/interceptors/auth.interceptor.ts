import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { API_BASE_URL } from '../services/api-config';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const baseUrl = inject(API_BASE_URL);
  const token = auth.token();

  // A7: el token solo viaja hacia nuestro propio backend. Sin este chequeo, cualquier
  // petición futura a un tercero (CDN, proxy de imágenes, el LLM directamente) se
  // llevaría la sesión del usuario sin que nadie lo haya decidido explícitamente.
  const isOwnApi = req.url.startsWith(baseUrl);

  const authed = token && isOwnApi
    ? req.clone({
        setHeaders: { Authorization: `Bearer ${token}` },
      })
    : req;

  // BUG-12: un 401 en la propia petición de login es una respuesta de negocio normal
  // (credenciales incorrectas), no una sesión que expiró — no debe disparar logout()
  // (que navega a /login sin el `returnUrl`, perdiendo la redirección original).
  const isLoginRequest = req.url.endsWith('/auth/login');

  return next(authed).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401 && !isLoginRequest) {
        auth.logout();
      }
      return throwError(() => err);
    }),
  );
};
