import { SupervisorCard } from '../models';

export interface ApiSupervisor {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  status: 'active' | 'inactive';
  contribution: string | number;
  losses: string | number;
  photo_url: string | null;
  created_at: string;
  agent_count: number;
}

export type ApiSupervisorPatch = Partial<{
  first_name: string;
  last_name: string;
  phone: string | null;
  city: string | null;
  status: 'active' | 'inactive';
  contribution: number;
  losses: number;
  photo_url: string;
}>;

export function toSupervisorCard(api: ApiSupervisor): SupervisorCard {
  return {
    id: api.id,
    fullName: `${api.first_name} ${api.last_name}`.trim(),
    status: api.status,
    contribution: Number(api.contribution),
    losses: Number(api.losses),
    photoUrl: api.photo_url ?? '',
    createdAt: api.created_at,
    agentCount: api.agent_count ?? 0,
  };
}

export function fromSupervisorCardPartial(
  partial: Partial<SupervisorCard>,
): ApiSupervisorPatch {
  const out: ApiSupervisorPatch = {};
  if (partial.fullName !== undefined) {
    const [first, ...rest] = partial.fullName.split(' ');
    out.first_name = first;
    out.last_name = rest.join(' ');
  }
  if (partial.status !== undefined) out.status = partial.status;
  if (partial.contribution !== undefined) out.contribution = partial.contribution;
  if (partial.losses !== undefined) out.losses = partial.losses;
  if (partial.photoUrl !== undefined) out.photo_url = partial.photoUrl;
  return out;
}
