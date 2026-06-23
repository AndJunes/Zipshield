import { AuthSession, AuthUser } from '../models';

export interface ApiUser {
  id: number;
  email: string;
  role: 'admin' | 'supervisor' | 'agent' | 'client';
  ref_id: number | null;
  first_name: string;
  last_name: string;
  photo_url: string | null;
}

export interface ApiSession {
  token: string;
  user: ApiUser;
  expires_at: string;
}

export function toAuthUser(api: ApiUser): AuthUser {
  return {
    id: api.id,
    firstName: api.first_name,
    lastName: api.last_name,
    email: api.email,
    role: api.role,
    refId: api.ref_id,
    photoUrl: api.photo_url ?? '',
  };
}

export function toAuthSession(api: ApiSession): AuthSession {
  return {
    token: api.token,
    user: toAuthUser(api.user),
    expiresAt: api.expires_at,
  };
}
