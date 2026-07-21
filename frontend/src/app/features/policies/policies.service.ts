import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { Policy, PolicyEvent, PolicyInput, PolicyQuote, QuoteInput } from '../../core/models';
import { API_BASE_URL } from '../../core/services/api-config';
import {
  ApiPolicy,
  ApiPolicyEvent,
  ApiQuote,
  fromPolicyCreate,
  fromQuoteRequest,
  toPolicy,
  toPolicyEvent,
  toQuote,
} from '../../core/adapters/policy.adapter';

@Injectable({ providedIn: 'root' })
export class PoliciesService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<Policy[]> {
    return this.http
      .get<ApiPolicy[]>(`${this.baseUrl}/policies`)
      .pipe(map((items) => items.map(toPolicy)));
  }

  getById(id: number): Observable<Policy> {
    return this.http.get<ApiPolicy>(`${this.baseUrl}/policies/${id}`).pipe(map(toPolicy));
  }

  events(id: number): Observable<PolicyEvent[]> {
    return this.http
      .get<ApiPolicyEvent[]>(`${this.baseUrl}/policies/${id}/events`)
      .pipe(map((items) => items.map(toPolicyEvent)));
  }

  quote(input: QuoteInput): Observable<PolicyQuote> {
    return this.http
      .post<ApiQuote>(`${this.baseUrl}/policies/quote`, fromQuoteRequest(input))
      .pipe(map(toQuote));
  }

  create(input: PolicyInput): Observable<Policy> {
    return this.http
      .post<ApiPolicy>(`${this.baseUrl}/policies`, fromPolicyCreate(input))
      .pipe(map(toPolicy));
  }

  cancel(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/policies/${id}`);
  }
}
