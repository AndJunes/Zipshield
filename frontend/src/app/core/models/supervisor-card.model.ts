export type SupervisorStatus = 'active' | 'inactive';

export interface SupervisorCard {
  id: number;
  fullName: string;
  status: SupervisorStatus;
  contribution: number;
  losses: number;
  photoUrl: string;
  createdAt: string;
  agentCount: number;
}
