export interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  client_number: string;
  status: string;
  agent_id: number;
}

export interface ClientCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  city?: string | null;
  client_number: string;
  status?: string;
  agent_id: number;
}
