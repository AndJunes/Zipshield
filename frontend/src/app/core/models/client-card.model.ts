export type ClientStatus = 'active' | 'inactive';

export interface ClientHistory {
  pastClaimCount: number;
  acceptClaim: number;
  manualReviewClaim: number;
  rejectedClaim: number;
  last90DaysClaimCount: number;
  historyFlags: string[];
  historySummary: string;
}

export interface ClientCard {
  id: number;
  userId: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  city: string | null;
  clientNumber: string;
  status: ClientStatus;
  agentId: number;
  photoUrl: string;
  history: ClientHistory;
}
