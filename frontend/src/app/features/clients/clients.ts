import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AgentCard, ClientCard } from '../../core/models';
import { AgentsService } from '../agents/agents.service';
import { ClientsService } from './clients.service';
import { formatRiskFlag } from '../../shared/utils/claim-labels';

const RADIUS = 50;

interface DonutSegment {
  label: string;
  value: number;
  color: string;
  dashArray: string;
  dashOffset: number;
}

interface DonutChart {
  title: string;
  total: number;
  segments: DonutSegment[];
}

interface AgentClientsRow {
  id: number;
  fullName: string;
  count: number;
}

interface CityRow {
  city: string;
  count: number;
}

@Component({
  selector: 'app-clients',
  imports: [RouterLink],
  templateUrl: './clients.html',
})
export class Clients {
  private readonly clientsService = inject(ClientsService);
  private readonly agentsService = inject(AgentsService);

  readonly clients = signal<ClientCard[]>([]);
  readonly agents = signal<AgentCard[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly circumference = 2 * Math.PI * RADIUS;

  readonly totalCount = computed(() => this.clients().length);
  readonly activeCount = computed(
    () => this.clients().filter((c) => c.status === 'active').length,
  );
  readonly inactiveCount = computed(() => this.totalCount() - this.activeCount());
  readonly noClaimsCount = computed(
    () => this.clients().filter((c) => c.history.pastClaimCount === 0).length,
  );
  readonly withClaimsCount = computed(() => this.totalCount() - this.noClaimsCount());
  readonly riskCount = computed(
    () => this.clients().filter((c) => c.history.historyFlags.length > 0).length,
  );
  readonly cleanCount = computed(() => this.totalCount() - this.riskCount());

  readonly totalPastClaims = computed(() =>
    this.clients().reduce((s, c) => s + c.history.pastClaimCount, 0),
  );
  readonly totalAccepted = computed(() =>
    this.clients().reduce((s, c) => s + c.history.acceptClaim, 0),
  );
  readonly totalManualReview = computed(() =>
    this.clients().reduce((s, c) => s + c.history.manualReviewClaim, 0),
  );
  readonly totalRejected = computed(() =>
    this.clients().reduce((s, c) => s + c.history.rejectedClaim, 0),
  );
  readonly totalLast90Days = computed(() =>
    this.clients().reduce((s, c) => s + c.history.last90DaysClaimCount, 0),
  );

  readonly statusChart = computed<DonutChart>(() =>
    this.buildChart('Por estado', [
      { label: 'Activos', value: this.activeCount(), color: 'var(--color-color4)' },
      { label: 'Inactivos', value: this.inactiveCount(), color: 'var(--color-color3)' },
    ]),
  );

  readonly riskChart = computed<DonutChart>(() =>
    this.buildChart('Por nivel de riesgo', [
      { label: 'Sin observaciones', value: this.cleanCount(), color: 'var(--color-color4)' },
      { label: 'Con riesgo', value: this.riskCount(), color: 'var(--color-color2)' },
    ]),
  );

  readonly activityChart = computed<DonutChart>(() =>
    this.buildChart('Por actividad', [
      { label: 'Con reclamos', value: this.withClaimsCount(), color: 'var(--color-color4)' },
      { label: 'Sin reclamos', value: this.noClaimsCount(), color: 'var(--color-color3)' },
    ]),
  );

  readonly outcomeChart = computed<DonutChart>(() =>
    this.buildChart('Resolución histórica de reclamos', [
      { label: 'Aceptados', value: this.totalAccepted(), color: 'var(--color-color4)' },
      { label: 'Revisión manual', value: this.totalManualReview(), color: 'var(--color-color3)' },
      { label: 'Rechazados', value: this.totalRejected(), color: 'var(--color-color2)' },
    ]),
  );

  readonly charts = computed<DonutChart[]>(() => [
    this.statusChart(),
    this.riskChart(),
    this.activityChart(),
    this.outcomeChart(),
  ]);

  readonly historyFlagCounts = computed(() => {
    const counts: Record<string, number> = {};
    this.clients().forEach((c) =>
      c.history.historyFlags.forEach((f) => {
        counts[f] = (counts[f] ?? 0) + 1;
      }),
    );
    return Object.entries(counts)
      .map(([flag, count]) => ({ flag, count }))
      .sort((a, b) => b.count - a.count);
  });

  readonly historyFlagMax = computed(() => {
    const max = Math.max(...this.historyFlagCounts().map((f) => f.count), 0);
    return max === 0 ? 1 : max;
  });

  readonly clientsByAgent = computed<AgentClientsRow[]>(() => {
    const list = this.clients();
    const result = this.agents().map((a) => ({
      id: a.id,
      fullName: a.fullName,
      count: list.filter((c) => c.agentId === a.id).length,
    }));
    return result.sort((a, b) => b.count - a.count);
  });

  readonly clientsByAgentMax = computed(() => {
    const max = Math.max(...this.clientsByAgent().map((r) => r.count), 0);
    return max === 0 ? 1 : max;
  });

  readonly clientsByCity = computed<CityRow[]>(() => {
    const counts: Record<string, number> = {};
    this.clients().forEach((c) => {
      const city = c.city ?? 'Sin ciudad';
      counts[city] = (counts[city] ?? 0) + 1;
    });
    return Object.entries(counts)
      .map(([city, count]) => ({ city, count }))
      .sort((a, b) => b.count - a.count);
  });

  readonly clientsByCityMax = computed(() => {
    const max = Math.max(...this.clientsByCity().map((r) => r.count), 0);
    return max === 0 ? 1 : max;
  });

  constructor() {
    this.clientsService.list().subscribe({
      next: (data) => {
        this.clients.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message ?? 'No se pudieron cargar los clientes');
        this.loading.set(false);
      },
    });
    this.agentsService.list().subscribe({
      next: (data) => this.agents.set(data),
      error: () => undefined,
    });
  }

  historyFlagWidth(count: number): number {
    return (count / this.historyFlagMax()) * 100;
  }

  agentBarWidth(count: number): number {
    return (count / this.clientsByAgentMax()) * 100;
  }

  cityBarWidth(count: number): number {
    return (count / this.clientsByCityMax()) * 100;
  }

  private buildChart(
    title: string,
    items: { label: string; value: number; color: string }[],
  ): DonutChart {
    const total = items.reduce((s, i) => s + i.value, 0);
    if (total === 0) {
      return {
        title,
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
    return { title, total, segments };
  }

  readonly formatRiskFlag = formatRiskFlag;
}
