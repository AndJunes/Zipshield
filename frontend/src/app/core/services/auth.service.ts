import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, map, tap, throwError } from 'rxjs';

import { ApiSession, toAuthSession } from '../adapters/auth.adapter';
import { AuthCredentials, AuthSession, AuthUser } from '../models';
import { API_BASE_URL } from './api-config';
import { SessionStorageService } from './session-storage.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly storage = inject(SessionStorageService);
  private readonly router = inject(Router);

  private readonly _session = signal<AuthSession | null>(null);

  readonly currentUser = computed<AuthUser | null>(
    () => this._session()?.user ?? null,
  );
  readonly token = computed<string | null>(() => this._session()?.token ?? null);
  readonly isAuthenticated = computed(() => this._session() !== null);

  constructor() {
    const stored = this.storage.get();
    if (stored) {
      this._session.set(stored);
    }
  }

  login(credentials: AuthCredentials): Observable<AuthSession> {
    return this.http
      .post<ApiSession>(`${this.baseUrl}/auth/login`, credentials)
      .pipe(
        map(toAuthSession),
        tap((session) => {
          this.storage.set(session);
          this._session.set(session);
        }),
        catchError((err) =>
          throwError(
            () =>
              new Error(
                err?.error?.detail ?? err?.message ?? 'Credenciales inválidas',
              ),
          ),
        ),
      );
  }

  logout(): void {
    this.storage.clear();
    this._session.set(null);
    this.router.navigateByUrl('/login');
  }
}
