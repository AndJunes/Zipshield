import { Routes } from '@angular/router';
import { DashboardLayout } from './layouts/dashboard-layout/dashboard-layout';
import {
  adminOnlyGuard,
  adminOrSupervisorGuard,
} from './core/guards/admin-only.guard';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    component: DashboardLayout,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () => import('./features/home/home').then((m) => m.Home),
      },
      {
        path: 'supervisors',
        canActivate: [adminOnlyGuard],
        loadComponent: () =>
          import('./features/supervisors/supervisors').then((m) => m.Supervisors),
      },
      {
        path: 'supervisors/details',
        canActivate: [adminOnlyGuard],
        loadComponent: () =>
          import(
            './features/supervisors/supervisors-details/supervisors-details'
          ).then((m) => m.SupervisorsDetails),
      },
      {
        path: 'supervisors/details/:id',
        canActivate: [adminOnlyGuard],
        loadComponent: () =>
          import(
            './features/supervisors/supervisor-detail/supervisor-detail'
          ).then((m) => m.SupervisorDetail),
      },
      {
        path: 'agents',
        canActivate: [adminOrSupervisorGuard],
        loadComponent: () =>
          import('./features/agents/agents').then((m) => m.Agents),
      },
      {
        path: 'agents/details',
        canActivate: [adminOrSupervisorGuard],
        loadComponent: () =>
          import('./features/agents/agents-details/agents-details').then(
            (m) => m.AgentsDetails,
          ),
      },
      {
        path: 'agents/details/:id',
        canActivate: [adminOrSupervisorGuard],
        loadComponent: () =>
          import('./features/agents/agent-detail/agent-detail').then(
            (m) => m.AgentDetail,
          ),
      },
      {
        path: 'claims',
        loadComponent: () =>
          import('./features/claims/claims').then((m) => m.Claims),
      },
      {
        path: 'claims/details',
        loadComponent: () =>
          import('./features/claims/claims-details/claims-details').then(
            (m) => m.ClaimsDetails,
          ),
      },
      {
        path: 'claims/details/:id',
        loadComponent: () =>
          import('./features/claims/claim-detail/claim-detail').then(
            (m) => m.ClaimDetail,
          ),
      },
      {
        path: 'clients',
        loadComponent: () =>
          import('./features/clients/clients').then((m) => m.Clients),
      },
      {
        path: 'clients/details',
        loadComponent: () =>
          import('./features/clients/clients-details/clients-details').then(
            (m) => m.ClientsDetails,
          ),
      },
      {
        path: 'clients/details/:id',
        loadComponent: () =>
          import('./features/clients/client-detail/client-detail').then(
            (m) => m.ClientDetail,
          ),
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./features/profile/profile').then((m) => m.Profile),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/settings/settings').then((m) => m.Settings),
      },
    ],
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/login/login').then((m) => m.Login),
  },
];
