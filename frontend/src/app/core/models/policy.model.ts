export type PolicyType = 'car' | 'laptop' | 'package';

export type PolicyStatus =
  | 'quote'
  | 'underwriting'
  | 'in_force'
  | 'pending_cancel'
  | 'cancelled'
  | 'expired'
  | 'declined';

export interface Coverage {
  code: string;
  name: string;
  limitAmount: string;
  deductible: string;
  premium: string;
}

export interface Policy {
  id: number;
  clientId: number;
  type: PolicyType;
  name: string;
  status: PolicyStatus;
  effectiveDate: string;
  expirationDate: string;
  cancelDate: string | null;
  cancelReason: string | null;
  sumInsured: string;
  deductible: string;
  netPremium: string;
  taxesFees: string;
  price: string; // prima total
  coverage: string | null;
  coverages: Coverage[];
}

export interface PolicyEvent {
  id: number;
  eventType: string;
  fromStatus: string | null;
  toStatus: string | null;
  payload: Record<string, unknown>;
  createdAt: string;
}

export interface PolicyQuote {
  coverages: Coverage[];
  netPremium: string;
  taxesFees: string;
  totalPremium: string;
  baseRate: string;
  riskFactor: string;
}

export interface PolicyInput {
  clientId: number;
  type: PolicyType;
  name: string;
  sumInsured: number | string;
  deductible: number | string;
  effectiveDate: string;
  termMonths: number;
  coverage?: string | null;
}

export interface QuoteInput {
  type: PolicyType;
  sumInsured: number | string;
  clientId?: number | null;
}
