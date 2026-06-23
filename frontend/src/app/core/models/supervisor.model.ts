export interface Supervisor {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  status: string;
  created_at: string;
}

export interface SupervisorCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  city?: string | null;
  status?: string;
}

export interface SupervisorUpdate {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  city?: string | null;
  status?: string | null;
}
