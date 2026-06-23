import { AgentCard } from '../../core/models';

export type MockAgent = Omit<AgentCard, 'clientCount' | 'claims'>;

export const MOCK_AGENTS_BASE: MockAgent[] = [
  { id: 1, fullName: 'Mateo Aguirre', status: 'active', contribution: 78_400, losses: 78_000, photoUrl: 'https://i.pravatar.cc/300?u=a1', createdAt: '2026-06-22T07:30:00Z', supervisorId: 1 },
  { id: 2, fullName: 'Renata Paredes', status: 'active', contribution: 92_100, losses: 30_000, photoUrl: 'https://i.pravatar.cc/300?u=a2', createdAt: '2026-06-22T13:00:00Z', supervisorId: 2 },
  { id: 3, fullName: 'Bruno Lagos', status: 'inactive', contribution: 24_500, losses: 0, photoUrl: 'https://i.pravatar.cc/300?u=a3', createdAt: '2026-06-20T08:00:00Z', supervisorId: 3 },
  { id: 4, fullName: 'Florencia Núñez', status: 'active', contribution: 134_600, losses: 55_000, photoUrl: 'https://i.pravatar.cc/300?u=a4', createdAt: '2026-06-17T10:30:00Z', supervisorId: 4 },
  { id: 5, fullName: 'Iván Espinoza', status: 'active', contribution: 64_900, losses: 35_000, photoUrl: 'https://i.pravatar.cc/300?u=a5', createdAt: '2026-06-12T14:00:00Z', supervisorId: 5 },
  { id: 6, fullName: 'Paula Cisneros', status: 'inactive', contribution: 18_200, losses: 23_000, photoUrl: 'https://i.pravatar.cc/300?u=a6', createdAt: '2026-06-02T11:00:00Z', supervisorId: 6 },
  { id: 7, fullName: 'Hugo Almeida', status: 'active', contribution: 105_300, losses: 20_000, photoUrl: 'https://i.pravatar.cc/300?u=a7', createdAt: '2026-05-20T09:15:00Z', supervisorId: 7 },
  { id: 8, fullName: 'Sara Quiroga', status: 'active', contribution: 47_800, losses: 13_000, photoUrl: 'https://i.pravatar.cc/300?u=a8', createdAt: '2026-04-08T16:00:00Z', supervisorId: 8 },
  { id: 9, fullName: 'Leandro Bustos', status: 'active', contribution: 156_900, losses: 57_000, photoUrl: 'https://i.pravatar.cc/300?u=a9', createdAt: '2026-01-15T10:00:00Z', supervisorId: 9 },
  { id: 10, fullName: 'Antonella Ríos', status: 'active', contribution: 88_400, losses: 23_000, photoUrl: 'https://i.pravatar.cc/300?u=a10', createdAt: '2025-11-22T13:00:00Z', supervisorId: 10 },
  { id: 11, fullName: 'Gonzalo Pereyra', status: 'inactive', contribution: 12_900, losses: 0, photoUrl: 'https://i.pravatar.cc/300?u=a11', createdAt: '2025-09-05T08:30:00Z', supervisorId: 1 },
  { id: 12, fullName: 'Daniela Cárdenas', status: 'active', contribution: 71_600, losses: 16_000, photoUrl: 'https://i.pravatar.cc/300?u=a12', createdAt: '2025-07-10T11:00:00Z', supervisorId: 2 },
];
