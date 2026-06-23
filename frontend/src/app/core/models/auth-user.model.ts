export type UserRole = 'admin' | 'supervisor' | 'agent' | 'client';

export interface AuthUser {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  refId: number | null;
  photoUrl: string;
}
