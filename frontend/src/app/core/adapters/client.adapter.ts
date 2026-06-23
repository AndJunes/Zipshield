import { ClientCard } from '../models';

export interface ApiClientHistory {
  past_claim_count: number;
  accept_claim: number;
  manual_review_claim: number;
  rejected_claim: number;
  last_90_days_claim_count: number;
  history_flags: string[];
  history_summary: string | null;
}

export interface ApiClient {
  id: number;
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  client_number: string;
  status: 'active' | 'inactive';
  photo_url: string | null;
  agent_id: number;
  history: ApiClientHistory;
}

export type ApiClientPatch = Partial<{
  first_name: string;
  last_name: string;
  phone: string | null;
  city: string | null;
  status: 'active' | 'inactive';
  photo_url: string;
  agent_id: number;
}>;

export interface ApiClientCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  client_number: string;
  status: 'active' | 'inactive';
  photo_url: string;
  agent_id: number;
}

export function toClientCard(api: ApiClient): ClientCard {
  return {
    id: api.id,
    userId: api.user_id,
    firstName: api.first_name,
    lastName: api.last_name,
    email: api.email,
    phone: api.phone,
    city: api.city,
    clientNumber: api.client_number,
    status: api.status,
    photoUrl: api.photo_url ?? '',
    agentId: api.agent_id,
    history: {
      pastClaimCount: api.history.past_claim_count,
      acceptClaim: api.history.accept_claim,
      manualReviewClaim: api.history.manual_review_claim,
      rejectedClaim: api.history.rejected_claim,
      last90DaysClaimCount: api.history.last_90_days_claim_count,
      historyFlags: api.history.history_flags ?? [],
      historySummary: api.history.history_summary ?? '',
    },
  };
}

export function fromClientCardPartial(partial: Partial<ClientCard>): ApiClientPatch {
  const out: ApiClientPatch = {};
  if (partial.firstName !== undefined) out.first_name = partial.firstName;
  if (partial.lastName !== undefined) out.last_name = partial.lastName;
  if (partial.phone !== undefined) out.phone = partial.phone;
  if (partial.city !== undefined) out.city = partial.city;
  if (partial.status !== undefined) out.status = partial.status;
  if (partial.photoUrl !== undefined) out.photo_url = partial.photoUrl;
  if (partial.agentId !== undefined) out.agent_id = partial.agentId;
  return out;
}

export function fromClientCardCreate(
  input: Omit<ClientCard, 'id' | 'userId' | 'history'>,
): ApiClientCreate {
  return {
    first_name: input.firstName,
    last_name: input.lastName,
    email: input.email,
    phone: input.phone,
    city: input.city,
    client_number: input.clientNumber,
    status: input.status,
    photo_url: input.photoUrl,
    agent_id: input.agentId,
  };
}
