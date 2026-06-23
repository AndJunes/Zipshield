import { Component, computed, inject, signal } from '@angular/core';
import { DecimalPipe, PercentPipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import {
  AgentCard,
  ClaimCase,
  ClaimCaseStatus,
  ClaimObject,
} from '../../core/models';
import { AgentsService } from '../agents/agents.service';
import { ClaimsService } from './claims.service';
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

interface AgentClaimsRow {
  id: number;
  fullName: string;
  resolved: number;
  inProgress: number;
  total: number;
}

@Component({
  selector: 'app-claims',
  imports: [RouterLink, DecimalPipe, PercentPipe],
  templateUrl: './claims.html',
})
export class Claims {
  private readonly agentsService = inject(AgentsService);
  private readonly claimsService = inject(ClaimsService);

  readonly cases = signal<ClaimCase[]>([]);
  readonly agents = signal<AgentCard[]>([]);
  readonly circumference = 2 * Math.PI * RADIUS;

  readonly total = computed(() => this.cases().length);

  readonly objectChart = computed<DonutChart>(() => {
    const cases = this.cases();
    return this.buildChart('Por objeto', [
      { label: 'Auto', value: this.countObject(cases, 'car'), color: 'var(--color-color2)' },
      { label: 'Laptop', value: this.countObject(cases, 'laptop'), color: 'var(--color-color4)' },
      { label: 'Paquete', value: this.countObject(cases, 'package'), color: 'var(--color-color3)' },
    ]);
  });

  readonly statusChart = computed<DonutChart>(() => {
    const cases = this.cases();
    return this.buildChart('Por resultado', [
      { label: 'Soportado', value: this.countStatus(cases, 'supported'), color: 'var(--color-color4)' },
      { label: 'Contradicho', value: this.countStatus(cases, 'contradicted'), color: 'var(--color-color2)' },
      { label: 'Sin evidencia', value: this.countStatus(cases, 'not_enough_information'), color: 'var(--color-color3)' },
    ]);
  });

  readonly severityChart = computed<DonutChart>(() => {
    const cases = this.cases();
    return this.buildChart('Por severidad', [
      { label: 'Alta', value: this.countSeverity(cases, 'high'), color: 'var(--color-color2)' },
      { label: 'Media', value: this.countSeverity(cases, 'medium'), color: 'var(--color-color4)' },
      { label: 'Baja', value: this.countSeverity(cases, 'low'), color: '#a3a3d3' },
      { label: 'Desconocida', value: this.countSeverity(cases, 'unknown'), color: 'var(--color-color3)' },
      { label: 'Ninguna', value: this.countSeverity(cases, 'none'), color: '#cfd2d8' },
    ]);
  });

  readonly evidenceChart = computed<DonutChart>(() => {
    const cases = this.cases();
    return this.buildChart('Estándar de evidencia', [
      { label: 'Cumple', value: cases.filter((c) => c.evidenceStandardMet).length, color: 'var(--color-color4)' },
      { label: 'No cumple', value: cases.filter((c) => !c.evidenceStandardMet).length, color: 'var(--color-color3)' },
    ]);
  });

  readonly validImageChart = computed<DonutChart>(() => {
    const cases = this.cases();
    return this.buildChart('Imagen válida', [
      { label: 'Válida', value: cases.filter((c) => c.validImage).length, color: 'var(--color-color4)' },
      { label: 'No válida', value: cases.filter((c) => !c.validImage).length, color: 'var(--color-color2)' },
    ]);
  });

  readonly charts = computed<DonutChart[]>(() => [
    this.objectChart(),
    this.statusChart(),
    this.severityChart(),
    this.evidenceChart(),
    this.validImageChart(),
  ]);

  readonly riskFlagCounts = computed(() => {
    const counts: Record<string, number> = {};
    this.cases().forEach((c) =>
      c.riskFlags.forEach((f) => {
        if (f === 'none') return;
        counts[f] = (counts[f] ?? 0) + 1;
      }),
    );
    return Object.entries(counts)
      .map(([flag, count]) => ({ flag, count }))
      .sort((a, b) => b.count - a.count);
  });

  readonly riskFlagMax = computed(() => {
    const max = Math.max(...this.riskFlagCounts().map((f) => f.count), 0);
    return max === 0 ? 1 : max;
  });

  readonly noRiskFlagsCount = computed(
    () => this.cases().filter((c) => c.riskFlags.length === 1 && c.riskFlags[0] === 'none').length,
  );

  readonly resolvedTotal = computed(() =>
    this.agents().reduce((s, c) => s + c.claims.resolved, 0),
  );
  readonly inProgressTotal = computed(() =>
    this.agents().reduce((s, c) => s + c.claims.inProgress, 0),
  );
  readonly grantedTotal = computed(() =>
    this.agents().reduce((s, c) => s + c.claims.granted, 0),
  );
  readonly rejectedTotal = computed(() =>
    this.agents().reduce((s, c) => s + c.claims.rejected, 0),
  );
  readonly claimsTotal = computed(
    () => this.resolvedTotal() + this.inProgressTotal(),
  );

  readonly resolvedRate = computed(() => {
    const t = this.claimsTotal();
    return t === 0 ? 0 : this.resolvedTotal() / t;
  });
  readonly grantedRate = computed(() => {
    const t = this.resolvedTotal();
    return t === 0 ? 0 : this.grantedTotal() / t;
  });

  readonly statusArc = computed(() => {
    const total = this.claimsTotal();
    return total === 0 ? 0 : this.circumference * (this.resolvedTotal() / total);
  });
  readonly statusArcRest = computed(() => this.circumference - this.statusArc());

  readonly outcomeArc = computed(() => {
    const total = this.resolvedTotal();
    return total === 0 ? 0 : this.circumference * (this.grantedTotal() / total);
  });
  readonly outcomeArcRest = computed(() => this.circumference - this.outcomeArc());

  readonly byAgent = computed<AgentClaimsRow[]>(() =>
    [...this.agents()]
      .map((c) => ({
        id: c.id,
        fullName: c.fullName,
        resolved: c.claims.resolved,
        inProgress: c.claims.inProgress,
        total: c.claims.resolved + c.claims.inProgress,
      }))
      .sort((a, b) => b.total - a.total),
  );

  readonly byAgentMax = computed(() => {
    const max = Math.max(...this.byAgent().map((r) => r.total), 0);
    return max === 0 ? 1 : max;
  });

  constructor() {
    this.agentsService.list().subscribe({
      next: (data) => this.agents.set(data),
      error: () => undefined,
    });
    this.claimsService.list().subscribe({
      next: (data) => this.cases.set(data),
      error: () => undefined,
    });
  }

  resolvedWidth(n: number): number {
    return (n / this.byAgentMax()) * 100;
  }

  inProgressWidth(n: number): number {
    return (n / this.byAgentMax()) * 100;
  }

  private countObject(cases: ClaimCase[], obj: ClaimObject): number {
    return cases.filter((c) => c.object === obj).length;
  }

  private countStatus(cases: ClaimCase[], status: ClaimCaseStatus): number {
    return cases.filter((c) => c.claimStatus === status).length;
  }

  private countSeverity(cases: ClaimCase[], severity: string): number {
    return cases.filter((c) => c.severity === severity).length;
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

  riskFlagWidth(count: number): number {
    return (count / this.riskFlagMax()) * 100;
  }

  readonly formatRiskFlag = formatRiskFlag;
}
