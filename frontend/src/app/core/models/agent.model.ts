export interface Agent {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  city: string | null;
  agent_number: string;
  status: string;
  supervisor_id: number;
}

export interface AgentCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  city?: string | null;
  agent_number: string;
  status?: string;
  supervisor_id: number;
}
