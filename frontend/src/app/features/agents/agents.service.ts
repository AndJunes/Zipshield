import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { AgentCard } from '../../core/models';
import { API_BASE_URL } from '../../core/services/api-config';
import {
  ApiAgent,
  fromAgentCardPartial,
  toAgentCard,
} from '../../core/adapters/agent.adapter';

export type AgentInput = Omit<
  AgentCard,
  'id' | 'clientCount' | 'claims' | 'createdAt'
>;

@Injectable({ providedIn: 'root' })
export class AgentsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  list(): Observable<AgentCard[]> {
    return this.http
      .get<ApiAgent[]>(`${this.baseUrl}/agents`)
      .pipe(map((items) => items.map(toAgentCard)));
  }

  update(id: number, changes: Partial<AgentCard>): Observable<AgentCard> {
    return this.http
      .patch<ApiAgent>(`${this.baseUrl}/agents/${id}`, fromAgentCardPartial(changes))
      .pipe(map(toAgentCard));
  }

  create(input: AgentInput): Observable<AgentCard> {
    const [first, ...rest] = input.fullName.split(' ');
    const lastName = rest.join(' ');
    const payload = {
      first_name: first,
      last_name: lastName,
      email: `${first.toLowerCase()}.${lastName.toLowerCase().replace(/\s+/g, '')}@zipshield.io`,
      agent_number: `AGT-${Date.now().toString().slice(-6)}`,
      status: input.status,
      contribution: input.contribution,
      losses: input.losses,
      photo_url: input.photoUrl,
      supervisor_id: input.supervisorId,
    };
    return this.http
      .post<ApiAgent>(`${this.baseUrl}/agents`, payload)
      .pipe(map(toAgentCard));
  }
}
