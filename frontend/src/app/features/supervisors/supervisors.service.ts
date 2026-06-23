import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { SupervisorCard } from '../../core/models';
import { API_BASE_URL } from '../../core/services/api-config';
import {
  ApiSupervisor,
  ApiSupervisorPatch,
  fromSupervisorCardPartial,
  toSupervisorCard,
} from '../../core/adapters/supervisor.adapter';

export type SupervisorInput = Omit<SupervisorCard, 'id' | 'agentCount' | 'createdAt'>;

@Injectable({ providedIn: 'root' })
export class SupervisorsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<SupervisorCard[]> {
    return this.http
      .get<ApiSupervisor[]>(`${this.baseUrl}/supervisors`)
      .pipe(map((items) => items.map(toSupervisorCard)));
  }

  update(id: number, changes: Partial<SupervisorCard>): Observable<SupervisorCard> {
    return this.http
      .patch<ApiSupervisor>(
        `${this.baseUrl}/supervisors/${id}`,
        fromSupervisorCardPartial(changes),
      )
      .pipe(map(toSupervisorCard));
  }

  create(input: SupervisorInput): Observable<SupervisorCard> {
    const [first, ...rest] = input.fullName.split(' ');
    const payload: ApiSupervisorPatch & { email: string } = {
      first_name: first,
      last_name: rest.join(' '),
      email: `${first.toLowerCase()}.${rest.join('').toLowerCase() || 'sup'}@zipshield.io`,
      status: input.status,
      contribution: input.contribution,
      losses: input.losses,
      photo_url: input.photoUrl,
    };
    return this.http
      .post<ApiSupervisor>(`${this.baseUrl}/supervisors`, payload)
      .pipe(map(toSupervisorCard));
  }
}
