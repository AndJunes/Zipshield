import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { API_BASE_URL } from '../services/api-config';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const baseUrl = inject(API_BASE_URL);
  const token = auth.token();

  // The token only travels to our own backend. Without this check, any future
  // request to a third party (CDN, image proxy, the LLM directly) would carry the
  // user's session without anyone having explicitly decided that.
  const isOwnApi = req.url.startsWith(baseUrl);

  const authed = token && isOwnApi
    ? req.clone({
        setHeaders: { Authorization: `Bearer ${token}` },
      })
    : req;

  // A 401 on the login request itself is a normal business response (wrong
  // credentials), not an expired session — it must not trigger logout() (which
  // navigates to /login without the `returnUrl`, losing the original redirect).
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
