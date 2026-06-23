import { AgentCard } from '../models';

export interface ApiAgentClaims {
  resolved: number;
  in_progress: number;
  granted: number;
  rejected: number;
}

export interface ApiAgent {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  agent_number: string;
  status: 'active' | 'inactive';
  contribution: string | number;
  losses: string | number;
  photo_url: string | null;
  created_at: string;
  supervisor_id: number;
  client_count: number;
  claims: ApiAgentClaims;
}

export type ApiAgentPatch = Partial<{
  first_name: string;
  last_name: string;
  phone: string | null;
  city: string | null;
  status: 'active' | 'inactive';
  contribution: number;
  losses: number;
  photo_url: string;
  supervisor_id: number;
}>;

export function toAgentCard(api: ApiAgent): AgentCard {
  return {
    id: api.id,
    fullName: `${api.first_name} ${api.last_name}`.trim(),
    status: api.status,
    contribution: Number(api.contribution),
    losses: Number(api.losses),
    photoUrl: api.photo_url ?? '',
    createdAt: api.created_at,
    supervisorId: api.supervisor_id,
    clientCount: api.client_count ?? 0,
    claims: {
      resolved: api.claims?.resolved ?? 0,
      inProgress: api.claims?.in_progress ?? 0,
      granted: api.claims?.granted ?? 0,
      rejected: api.claims?.rejected ?? 0,
    },
  };
}

export function fromAgentCardPartial(partial: Partial<AgentCard>): ApiAgentPatch {
  const out: ApiAgentPatch = {};
  if (partial.fullName !== undefined) {
    const [first, ...rest] = partial.fullName.split(' ');
    out.first_name = first;
    out.last_name = rest.join(' ');
  }
  if (partial.status !== undefined) out.status = partial.status;
  if (partial.contribution !== undefined) out.contribution = partial.contribution;
  if (partial.losses !== undefined) out.losses = partial.losses;
  if (partial.photoUrl !== undefined) out.photo_url = partial.photoUrl;
  if (partial.supervisorId !== undefined) out.supervisor_id = partial.supervisorId;
  return out;
}
