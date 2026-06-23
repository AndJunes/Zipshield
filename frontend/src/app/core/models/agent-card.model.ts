export type AgentStatus = 'active' | 'inactive';

export interface AgentClaims {
  resolved: number;
  inProgress: number;
  granted: number;
  rejected: number;
}

export interface AgentCard {
  id: number;
  fullName: string;
  status: AgentStatus;
  contribution: number;
  losses: number;
  photoUrl: string;
  createdAt: string;
  supervisorId: number;
  clientCount: number;
  claims: AgentClaims;
}
