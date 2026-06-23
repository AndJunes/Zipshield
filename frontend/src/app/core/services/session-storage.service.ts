import { Injectable } from '@angular/core';

import { AuthSession } from '../models';

const STORAGE_KEY = 'zipshield:session';

@Injectable({ providedIn: 'root' })
export class SessionStorageService {
  get(): AuthSession | null {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw) as AuthSession;
      if (!parsed?.token || !parsed?.user || !parsed?.expiresAt) {
        return null;
      }
      if (new Date(parsed.expiresAt).getTime() <= Date.now()) {
        this.clear();
        return null;
      }
      return parsed;
    } catch {
      return null;
    }
  }

  set(session: AuthSession): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }

  clear(): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.removeItem(STORAGE_KEY);
  }
}
