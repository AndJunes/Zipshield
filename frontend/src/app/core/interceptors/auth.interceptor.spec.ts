import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { HttpErrorResponse, HttpRequest, HttpResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';
import { API_BASE_URL } from '../services/api-config';

const FAKE_API_BASE_URL = 'http://api.test';

describe('authInterceptor — BUG-12: returnUrl sobrevive a un login fallido', () => {
  function runInterceptor(url: string, authMock: Partial<AuthService>) {
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authMock },
        { provide: API_BASE_URL, useValue: FAKE_API_BASE_URL },
      ],
    });
    const req = new HttpRequest('POST', url, {});
    return TestBed.runInInjectionContext(() =>
      authInterceptor(req, () => throwError(() => new HttpErrorResponse({ status: 401 }))),
    );
  }

  it('NO llama a logout() cuando el 401 viene de la propia petición de login', async () => {
    const logout = vi.fn();
    const authMock: Partial<AuthService> = { token: signal(null), logout };

    await new Promise<void>((resolve) => {
      runInterceptor('http://api.test/auth/login', authMock).subscribe({ error: () => resolve() });
    });

    expect(logout).not.toHaveBeenCalled();
  });

  it('SÍ llama a logout() cuando el 401 viene de una ruta protegida cualquiera', async () => {
    const logout = vi.fn();
    const authMock: Partial<AuthService> = { token: signal(null), logout };

    await new Promise<void>((resolve) => {
      runInterceptor('http://api.test/claims', authMock).subscribe({ error: () => resolve() });
    });

    expect(logout).toHaveBeenCalledOnce();
  });
});

describe('authInterceptor — A7: el token solo viaja hacia nuestra propia API', () => {
  function runAndCaptureRequest(url: string, token: string | null) {
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { token: signal(token), logout: vi.fn() } },
        { provide: API_BASE_URL, useValue: FAKE_API_BASE_URL },
      ],
    });
    const req = new HttpRequest('GET', url, {});
    let seenRequest: HttpRequest<unknown> | undefined;
    return TestBed.runInInjectionContext(() =>
      authInterceptor(req, (r) => {
        seenRequest = r;
        return of(new HttpResponse({ status: 200 }));
      }),
    ).toPromise().then(() => seenRequest);
  }

  it('adjunta el header Authorization en una petición al propio backend', async () => {
    const seen = await runAndCaptureRequest(`${FAKE_API_BASE_URL}/claims`, 'tok-123');
    expect(seen?.headers.get('Authorization')).toBe('Bearer tok-123');
  });

  it('NO adjunta el header Authorization en una petición a un host de terceros', async () => {
    const seen = await runAndCaptureRequest('https://cdn.example.com/image.png', 'tok-123');
    expect(seen?.headers.get('Authorization')).toBeNull();
  });
});
