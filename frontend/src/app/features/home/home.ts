import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, PercentPipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import {
  AgentCard,
  ClaimCase,
  ClientCard,
  SupervisorCard,
} from '../../core/models';
import { AuthService } from '../../core/services/auth.service';
import { SupervisorsService } from '../supervisors/supervisors.service';
import { AgentsService } from '../agents/agents.service';
import { ClientsService } from '../clients/clients.service';
import { ClaimsService } from '../claims/claims.service';

const RADIUS = 40;

interface DonutSegment {
  label: string;
  value: number;
  color: string;
  dashArray: string;
  dashOffset: number;
}

interface DonutChart {
  total: number;
  segments: DonutSegment[];
}

@Component({
  selector: 'app-home',
  imports: [CurrencyPipe, PercentPipe, RouterLink],
  templateUrl: './home.html',
})
export class Home {
  private readonly supervisorsService = inject(SupervisorsService);
  private readonly agentsService = inject(AgentsService);
  private readonly clientsService = inject(ClientsService);
  private readonly claimsService = inject(ClaimsService);
  private readonly authService = inject(AuthService);

  readonly isAdmin = computed(
    () => this.authService.currentUser()?.role === 'admin',
  );
  readonly isAgent = computed(
    () => this.authService.currentUser()?.role === 'agent',
  );
  readonly canSeeAgents = computed(
    () => !this.isAgent(),
  );

  readonly supervisors = signal<SupervisorCard[]>([]);
  readonly agents = signal<AgentCard[]>([]);
  readonly clients = signal<ClientCard[]>([]);
  readonly claims = signal<ClaimCase[]>([]);

  readonly circumference = 2 * Math.PI * RADIUS;

  readonly totalSupervisors = computed(() => this.supervisors().length);
  readonly totalAgents = computed(() => this.agents().length);
  readonly totalClients = computed(() => this.clients().length);
  readonly totalClaims = computed(() => this.claims().length);

  readonly activeAgents = computed(
    () => this.agents().filter((a) => a.status === 'active').length,
  );
  readonly activeClients = computed(
    () => this.clients().filter((c) => c.status === 'active').length,
  );

  readonly netResult = computed(() => {
    const gains = this.agents().reduce((s, a) => s + a.contribution, 0);
    const losses = this.agents().reduce((s, a) => s + a.losses, 0);
    return { gains, losses, net: gains - losses };
  });

  readonly claimStatusChart = computed<DonutChart>(() => {
    const cases = this.claims();
    const supported = cases.filter((c) => c.claimStatus === 'supported').length;
    const contradicted = cases.filter(
      (c) => c.claimStatus === 'contradicted',
    ).length;
    const pending = cases.filter(
      (c) => c.claimStatus === 'not_enough_information',
    ).length;
    return this.buildDonut([
      { label: 'Soportado', value: supported, color: 'var(--color-color4)' },
      { label: 'Contradicho', value: contradicted, color: 'var(--color-color2)' },
      { label: 'Sin evidencia', value: pending, color: 'var(--color-color3)' },
    ]);
  });

  readonly objectChart = computed<DonutChart>(() => {
    const cases = this.claims();
    return this.buildDonut([
      { label: 'Auto', value: cases.filter((c) => c.object === 'car').length, color: 'var(--color-color2)' },
      { label: 'Laptop', value: cases.filter((c) => c.object === 'laptop').length, color: 'var(--color-color4)' },
      { label: 'Paquete', value: cases.filter((c) => c.object === 'package').length, color: 'var(--color-color3)' },
    ]);
  });

  readonly topAgents = computed(() =>
    [...this.agents()]
      .sort((a, b) => b.contribution - a.contribution)
      .slice(0, 3),
  );

  readonly topSupervisors = computed(() =>
    [...this.supervisors()]
      .sort((a, b) => b.contribution - a.contribution)
      .slice(0, 3),
  );

  readonly topAgentMax = computed(
    () => this.topAgents()[0]?.contribution ?? 1,
  );
  readonly topSupervisorMax = computed(
    () => this.topSupervisors()[0]?.contribution ?? 1,
  );

  readonly riskClients = computed(
    () => this.clients().filter((c) => c.history.historyFlags.length > 0).length,
  );

  readonly resolvedRate = computed(() => {
    const total = this.claims().length;
    if (total === 0) return 0;
    const resolved = this.claims().filter(
      (c) => c.claimStatus !== 'not_enough_information',
    ).length;
    return resolved / total;
  });

  readonly recentClaims = computed(() =>
    [...this.claims()].slice(-5).reverse(),
  );

  constructor() {
    this.supervisorsService.list().subscribe((data) => this.supervisors.set(data));
    this.agentsService.list().subscribe((data) => this.agents.set(data));
    this.clientsService.list().subscribe((data) => this.clients.set(data));
    this.claimsService.list().subscribe((data) => this.claims.set(data));
  }

  topAgentBar(c: number): number {
    return (c / this.topAgentMax()) * 100;
  }

  topSupervisorBar(c: number): number {
    return (c / this.topSupervisorMax()) * 100;
  }

  private buildDonut(
    items: { label: string; value: number; color: string }[],
  ): DonutChart {
    const total = items.reduce((s, i) => s + i.value, 0);
    if (total === 0) {
      return {
        total: 0,
        segments: items.map((i) => ({
          ...i,
          dashArray: `0 ${this.circumference}`,
          dashOffset: 0,
        })),
      };
    }
    let cumulative = 0;
    const segments = items.map<DonutSegment>((item) => {
      const arc = (item.value / total) * this.circumference;
      const seg: DonutSegment = {
        ...item,
        dashArray: `${arc} ${this.circumference}`,
        dashOffset: -cumulative,
      };
      cumulative += arc;
      return seg;
    });
    return { total, segments };
  }
}
