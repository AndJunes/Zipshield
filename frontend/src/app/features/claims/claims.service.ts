import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, concatMap, first, map, of, switchMap, take, timer } from 'rxjs';

import { ClaimCase } from '../../core/models';
import { API_BASE_URL } from '../../core/services/api-config';
import {
  ApiClaim,
  fromClaimCreate,
  fromClaimPartial,
  toClaimCase,
} from '../../core/adapters/claim.adapter';

export type ClaimInput = Pick<
  ClaimCase,
  'object' | 'conversation' | 'imageUrls' | 'dateOfLoss'
> & { policyId: number };

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

  analyze(id: number): Observable<ClaimCase> {
    return this.http
      .post<ApiClaim>(`${this.baseUrl}/claims/${id}/analyze`, {})
      .pipe(
        map(toClaimCase),
        switchMap((claim) =>
          claim.analysisStatus === 'pending' ? this.pollAnalysis(id) : of(claim),
        ),
      );
  }

  // The analysis runs in the background on the server: poll until it leaves
  // "pending". A failed analysis (or running out of attempts) errors the stream,
  // which callers already treat as "could not analyze".
  private pollAnalysis(id: number): Observable<ClaimCase> {
    return timer(ClaimsService.ANALYSIS_POLL_MS, ClaimsService.ANALYSIS_POLL_MS).pipe(
      take(ClaimsService.ANALYSIS_POLL_LIMIT),
      concatMap(() =>
        this.http.get<ApiClaim>(`${this.baseUrl}/claims/${id}`).pipe(map(toClaimCase)),
      ),
      first((claim) => claim.analysisStatus !== 'pending'),
      map((claim) => {
        if (claim.analysisStatus === 'failed') {
          throw new Error(`Analysis of claim ${id} failed`);
        }
        return claim;
      }),
    );
  }

  private static readonly ANALYSIS_POLL_MS = 1500;
  private static readonly ANALYSIS_POLL_LIMIT = 240; // ~6 minutes in total
}
