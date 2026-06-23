import { AuthUser } from './auth-user.model';

export interface AuthSession {
  token: string;
  user: AuthUser;
  expiresAt: string;
}
