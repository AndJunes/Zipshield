import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { ClaimCase } from '../../core/models';
import { API_BASE_URL } from '../../core/services/api-config';
import {
  ApiClaim,
  fromClaimCreate,
  fromClaimPartial,
  toClaimCase,
} from '../../core/adapters/claim.adapter';

export type ClaimInput = Omit<
  ClaimCase,
  'id' | 'imageUrls' | 'supportingImageIds' | 'riskFlags'
>;

@Injectable({ providedIn: 'root' })
export class ClaimsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<ClaimCase[]> {
    return this.http
      .get<ApiClaim[]>(`${this.baseUrl}/claims`)
      .pipe(map((items) => items.map(toClaimCase)));
  }

  getById(id: number): Observable<ClaimCase | undefined> {
    return this.http
      .get<ApiClaim>(`${this.baseUrl}/claims/${id}`)
      .pipe(map(toClaimCase));
  }

  update(id: number, changes: Partial<ClaimCase>): Observable<ClaimCase> {
    return this.http
      .patch<ApiClaim>(`${this.baseUrl}/claims/${id}`, fromClaimPartial(changes))
      .pipe(map(toClaimCase));
  }

  create(input: ClaimInput): Observable<ClaimCase> {
    return this.http
      .post<ApiClaim>(`${this.baseUrl}/claims`, fromClaimCreate(input))
      .pipe(map(toClaimCase));
  }
}
