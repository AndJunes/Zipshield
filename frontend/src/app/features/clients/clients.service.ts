import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { ClientCard } from '../../core/models';
import { API_BASE_URL } from '../../core/services/api-config';
import {
  ApiClient,
  fromClientCardCreate,
  fromClientCardPartial,
  toClientCard,
} from '../../core/adapters/client.adapter';

export type ClientInput = Omit<ClientCard, 'id' | 'userId' | 'history'>;

@Injectable({ providedIn: 'root' })
export class ClientsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<ClientCard[]> {
    return this.http
      .get<ApiClient[]>(`${this.baseUrl}/clients`)
      .pipe(map((items) => items.map(toClientCard)));
  }

  getById(id: number): Observable<ClientCard | undefined> {
    return this.http
      .get<ApiClient>(`${this.baseUrl}/clients/${id}`)
      .pipe(map(toClientCard));
  }

  update(id: number, changes: Partial<ClientCard>): Observable<ClientCard> {
    return this.http
      .patch<ApiClient>(
        `${this.baseUrl}/clients/${id}`,
        fromClientCardPartial(changes),
      )
      .pipe(map(toClientCard));
  }

  create(input: ClientInput): Observable<ClientCard> {
    return this.http
      .post<ApiClient>(`${this.baseUrl}/clients`, fromClientCardCreate(input))
      .pipe(map(toClientCard));
  }
}
