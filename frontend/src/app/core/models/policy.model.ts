export type PolicyType = 'laptop' | 'automobile' | 'package';

export interface Policy {
  id: number;
  type: PolicyType;
  name: string;
  price: string;
  expiration_date: string;
  coverage: string | null;
  status: string;
  client_id: number;
}

export interface PolicyCreate {
  type: PolicyType;
  name: string;
  price: number | string;
  expiration_date: string;
  coverage?: string | null;
  status?: string;
  client_id: number;
}
