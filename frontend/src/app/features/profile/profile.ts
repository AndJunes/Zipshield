import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { AgentCard, SupervisorCard } from '../../core/models';
import { AuthService } from '../../core/services/auth.service';
import { SupervisorsService } from '../supervisors/supervisors.service';
import { AgentsService } from '../agents/agents.service';

@Component({
  selector: 'app-profile',
  imports: [RouterLink, CurrencyPipe, DatePipe],
  templateUrl: './profile.html',
})
export class Profile {
  private readonly authService = inject(AuthService);
  private readonly supervisorsService = inject(SupervisorsService);
  private readonly agentsService = inject(AgentsService);

  readonly user = this.authService.currentUser;

  readonly selfSupervisor = signal<SupervisorCard | null>(null);
  readonly selfAgent = signal<AgentCard | null>(null);
  readonly mySupervisor = signal<SupervisorCard | null>(null);

  readonly isAdmin = computed(() => this.user()?.role === 'admin');
  readonly isSupervisor = computed(() => this.user()?.role === 'supervisor');
  readonly isAgent = computed(() => this.user()?.role === 'agent');

  readonly supervisorNet = computed(() => {
    const s = this.selfSupervisor();
    return s ? s.contribution - s.losses : 0;
  });

  readonly agentNet = computed(() => {
    const a = this.selfAgent();
    return a ? a.contribution - a.losses : 0;
  });

  constructor() {
    const role = this.user()?.role;
    if (role === 'supervisor') {
      this.supervisorsService.list().subscribe((list) => {
        this.selfSupervisor.set(list[0] ?? null);
      });
    } else if (role === 'agent') {
      this.agentsService.list().subscribe((list) => {
        const me = list[0] ?? null;
        this.selfAgent.set(me);
        if (me) {
          this.supervisorsService.list().subscribe((sups) => {
            this.mySupervisor.set(
              sups.find((s) => s.id === me.supervisorId) ?? null,
            );
          });
        }
      });
    }
  }

  roleLabel(role: string): string {
    if (role === 'admin') return 'Administrador';
    if (role === 'supervisor') return 'Supervisor';
    if (role === 'agent') return 'Agente';
    if (role === 'client') return 'Cliente';
    return role;
  }
}
