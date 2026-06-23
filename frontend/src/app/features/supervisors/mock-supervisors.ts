import { SupervisorCard } from '../../core/models';

export type MockSupervisor = Omit<SupervisorCard, 'agentCount'>;

export const MOCK_SUPERVISORS_BASE: MockSupervisor[] = [
  { id: 1, fullName: 'María Fernández', status: 'active', contribution: 142_500, losses: 80_000, photoUrl: 'https://i.pravatar.cc/300?u=1', createdAt: '2026-06-22T08:15:00Z' },
  { id: 2, fullName: 'Carlos Méndez', status: 'active', contribution: 98_300, losses: 45_000, photoUrl: 'https://i.pravatar.cc/300?u=2', createdAt: '2026-06-22T11:40:00Z' },
  { id: 3, fullName: 'Sofía Ramírez', status: 'inactive', contribution: 54_200, losses: 30_000, photoUrl: 'https://i.pravatar.cc/300?u=3', createdAt: '2026-06-19T12:00:00Z' },
  { id: 4, fullName: 'Diego Salazar', status: 'active', contribution: 187_900, losses: 110_000, photoUrl: 'https://i.pravatar.cc/300?u=4', createdAt: '2026-06-16T09:00:00Z' },
  { id: 5, fullName: 'Lucía Vargas', status: 'active', contribution: 121_650, losses: 70_000, photoUrl: 'https://i.pravatar.cc/300?u=5', createdAt: '2026-06-10T11:00:00Z' },
  { id: 6, fullName: 'Andrés Cabrera', status: 'inactive', contribution: 43_800, losses: 50_000, photoUrl: 'https://i.pravatar.cc/300?u=6', createdAt: '2026-06-01T14:00:00Z' },
  { id: 7, fullName: 'Valentina Ortiz', status: 'active', contribution: 165_400, losses: 90_000, photoUrl: 'https://i.pravatar.cc/300?u=7', createdAt: '2026-05-15T14:00:00Z' },
  { id: 8, fullName: 'Javier Rojas', status: 'active', contribution: 89_750, losses: 40_000, photoUrl: 'https://i.pravatar.cc/300?u=8', createdAt: '2026-03-10T09:00:00Z' },
  { id: 9, fullName: 'Camila Torres', status: 'active', contribution: 203_100, losses: 95_000, photoUrl: 'https://i.pravatar.cc/300?u=9', createdAt: '2025-12-20T11:00:00Z' },
  { id: 10, fullName: 'Tomás Herrera', status: 'inactive', contribution: 31_200, losses: 35_000, photoUrl: 'https://i.pravatar.cc/300?u=10', createdAt: '2025-08-15T11:00:00Z' },
];
