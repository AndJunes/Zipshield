import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { UserRole } from '../../../core/models';
import { AuthService } from '../../../core/services/auth.service';

export interface SidebarItem {
  label: string;
  route: string;
  exact?: boolean;
  roles?: UserRole[];
}

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  private readonly authService = inject(AuthService);

  readonly items: SidebarItem[] = [
    { label: 'Dashboard', route: '/', exact: true },
    { label: 'Supervisores', route: '/supervisors', roles: ['admin'] },
    { label: 'Agentes', route: '/agents', roles: ['admin', 'supervisor'] },
    { label: 'Clientes', route: '/clients' },
    { label: 'Reclamos', route: '/claims' },
  ];

  readonly visibleItems = computed(() => {
    const role = this.authService.currentUser()?.role;
    return this.items.filter(
      (item) => !item.roles || (role !== undefined && item.roles.includes(role)),
    );
  });
}
