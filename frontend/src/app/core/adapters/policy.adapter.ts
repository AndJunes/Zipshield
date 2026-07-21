import {
  Coverage,
  Policy,
  PolicyEvent,
  PolicyInput,
  PolicyQuote,
  PolicyStatus,
  PolicyType,
  QuoteInput,
} from '../models';

export interface ApiCoverage {
  code: string;
  name: string;
  limit_amount: string;
  deductible: string;
  premium: string;
}

export interface ApiPolicy {
  id: number;
  client_id: number;
  type: PolicyType;
  name: string;
  status: PolicyStatus;
  effective_date: string;
  expiration_date: string;
  cancel_date: string | null;
  cancel_reason: string | null;
  sum_insured: string;
  deductible: string;
  net_premium: string;
  taxes_fees: string;
  price: string;
  coverage: string | null;
  coverages: ApiCoverage[];
}

export interface ApiPolicyEvent {
  id: number;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ApiQuote {
  coverages: ApiCoverage[];
  net_premium: string;
  taxes_fees: string;
  total_premium: string;
  base_rate: string;
  risk_factor: string;
}

export interface ApiPolicyCreate {
  client_id: number;
  type: PolicyType;
  name: string;
  sum_insured: number | string;
  deductible: number | string;
  effective_date: string;
  term_months: number;
  coverage?: string | null;
}

function toCoverage(c: ApiCoverage): Coverage {
  return {
    code: c.code,
    name: c.name,
    limitAmount: c.limit_amount,
    deductible: c.deductible,
    premium: c.premium,
  };
}

export function toPolicy(api: ApiPolicy): Policy {
  return {
    id: api.id,
    clientId: api.client_id,
    type: api.type,
    name: api.name,
    status: api.status,
    effectiveDate: api.effective_date,
    expirationDate: api.expiration_date,
    cancelDate: api.cancel_date,
    cancelReason: api.cancel_reason,
    sumInsured: api.sum_insured,
    deductible: api.deductible,
    netPremium: api.net_premium,
    taxesFees: api.taxes_fees,
    price: api.price,
    coverage: api.coverage,
    coverages: (api.coverages ?? []).map(toCoverage),
  };
}

export function toPolicyEvent(api: ApiPolicyEvent): PolicyEvent {
  return {
    id: api.id,
    eventType: api.event_type,
    fromStatus: api.from_status,
    toStatus: api.to_status,
    payload: api.payload ?? {},
    createdAt: api.created_at,
  };
}

export function toQuote(api: ApiQuote): PolicyQuote {
  return {
    coverages: (api.coverages ?? []).map(toCoverage),
    netPremium: api.net_premium,
    taxesFees: api.taxes_fees,
    totalPremium: api.total_premium,
    baseRate: api.base_rate,
    riskFactor: api.risk_factor,
  };
}

export function fromPolicyCreate(input: PolicyInput): ApiPolicyCreate {
  return {
    client_id: input.clientId,
    type: input.type,
    name: input.name,
    sum_insured: input.sumInsured,
    deductible: input.deductible,
    effective_date: input.effectiveDate,
    term_months: input.termMonths,
    coverage: input.coverage ?? null,
  };
}

export function fromQuoteRequest(input: QuoteInput): {
  type: PolicyType;
  sum_insured: number | string;
  client_id: number | null;
} {
  return {
    type: input.type,
    sum_insured: input.sumInsured,
    client_id: input.clientId ?? null,
  };
}
