import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { HttpErrorResponse, HttpRequest, HttpResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';
import { API_BASE_URL } from '../services/api-config';

const FAKE_API_BASE_URL = 'http://api.test';

describe('authInterceptor — returnUrl survives a failed login', () => {
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

  it('does NOT call logout() when the 401 comes from the login request itself', async () => {
    const logout = vi.fn();
    const authMock: Partial<AuthService> = { token: signal(null), logout };

    await new Promise<void>((resolve) => {
      runInterceptor('http://api.test/auth/login', authMock).subscribe({ error: () => resolve() });
    });

    expect(logout).not.toHaveBeenCalled();
  });

  it('DOES call logout() when the 401 comes from any protected route', async () => {
    const logout = vi.fn();
    const authMock: Partial<AuthService> = { token: signal(null), logout };

    await new Promise<void>((resolve) => {
      runInterceptor('http://api.test/claims', authMock).subscribe({ error: () => resolve() });
    });

    expect(logout).toHaveBeenCalledOnce();
  });
});

describe('authInterceptor — the token only travels to our own API', () => {
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

  it('attaches the Authorization header on a request to our own backend', async () => {
    const seen = await runAndCaptureRequest(`${FAKE_API_BASE_URL}/claims`, 'tok-123');
    expect(seen?.headers.get('Authorization')).toBe('Bearer tok-123');
  });

  it('does NOT attach the Authorization header on a request to a third-party host', async () => {
    const seen = await runAndCaptureRequest('https://cdn.example.com/image.png', 'tok-123');
    expect(seen?.headers.get('Authorization')).toBeNull();
  });
});
