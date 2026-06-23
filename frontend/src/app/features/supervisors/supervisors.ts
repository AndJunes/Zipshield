import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { SupervisorCard as SupervisorCardData } from '../../core/models';
import { SupervisorsService } from './supervisors.service';

const RADIUS = 50;

const DAY_MS = 24 * 60 * 60 * 1000;
const WEEK_MS = 7 * DAY_MS;
const MONTH_MS = 30 * DAY_MS;
const YEAR_MS = 365 * DAY_MS;

const EXCESS_THRESHOLD = 7;

interface JoinedBucket {
  label: string;
  count: number;
}

interface ContributionBucket {
  label: string;
  value: number;
}

type DistributionTone = 'empty' | 'normal' | 'excess';

interface DistributionBucket {
  label: string;
  count: number;
  tone: DistributionTone;
  match: (n: number) => boolean;
}

@Component({
  selector: 'app-supervisors',
  imports: [RouterLink, CurrencyPipe, DecimalPipe],
  templateUrl: './supervisors.html',
})
export class Supervisors {
  private readonly supervisorsService = inject(SupervisorsService);

  readonly cards = signal<SupervisorCardData[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly totalCount = computed(() => this.cards().length);
  readonly activeCount = computed(
    () => this.cards().filter((c) => c.status === 'active').length,
  );
  readonly inactiveCount = computed(() => this.totalCount() - this.activeCount());

  readonly circumference = 2 * Math.PI * RADIUS;
  readonly activeArc = computed(() => {
    const total = this.totalCount();
    return total === 0 ? 0 : this.circumference * (this.activeCount() / total);
  });
  readonly inactiveArc = computed(() => this.circumference - this.activeArc());

  private readonly buckets = computed(() => {
    const now = Date.now();
    return this.cards().map((c) => ({
      age: now - new Date(c.createdAt).getTime(),
      contribution: c.contribution,
    }));
  });

  readonly joined = computed<JoinedBucket[]>(() => {
    const items = this.buckets();
    const countIn = (ms: number) => items.filter((i) => i.age <= ms).length;
    return [
      { label: 'Hoy', count: countIn(DAY_MS) },
      { label: '7 días', count: countIn(WEEK_MS) },
      { label: '30 días', count: countIn(MONTH_MS) },
      { label: '1 año', count: countIn(YEAR_MS) },
    ];
  });

  readonly joinedMax = computed(() => {
    const max = Math.max(...this.joined().map((b) => b.count), 0);
    return max === 0 ? 1 : max;
  });

  readonly contribution = computed<ContributionBucket[]>(() => {
    const items = this.buckets();
    const sumIn = (ms: number) =>
      items.filter((i) => i.age <= ms).reduce((s, i) => s + i.contribution, 0);
    return [
      { label: 'Hoy', value: sumIn(DAY_MS) },
      { label: '7 días', value: sumIn(WEEK_MS) },
      { label: '30 días', value: sumIn(MONTH_MS) },
      { label: '1 año', value: sumIn(YEAR_MS) },
    ];
  });

  readonly contributionMax = computed(() => {
    const max = Math.max(...this.contribution().map((b) => b.value), 0);
    return max === 0 ? 1 : max;
  });

  readonly totalAgents = computed(() =>
    this.cards().reduce((sum, c) => sum + c.agentCount, 0),
  );
  readonly avgAgents = computed(() => {
    const n = this.cards().length;
    return n === 0 ? 0 : this.totalAgents() / n;
  });
  readonly emptySupervisors = computed(
    () => this.cards().filter((c) => c.agentCount === 0).length,
  );
  readonly excessSupervisors = computed(
    () => this.cards().filter((c) => c.agentCount >= EXCESS_THRESHOLD).length,
  );

  readonly distribution = computed<DistributionBucket[]>(() => {
    const def: Omit<DistributionBucket, 'count'>[] = [
      { label: '0', tone: 'empty', match: (n) => n === 0 },
      { label: '1-2', tone: 'normal', match: (n) => n >= 1 && n <= 2 },
      { label: '3-4', tone: 'normal', match: (n) => n >= 3 && n <= 4 },
      { label: '5-6', tone: 'normal', match: (n) => n >= 5 && n <= 6 },
      { label: `${EXCESS_THRESHOLD}+`, tone: 'excess', match: (n) => n >= EXCESS_THRESHOLD },
    ];
    const cards = this.cards();
    return def.map((d) => ({
      ...d,
      count: cards.filter((c) => d.match(c.agentCount)).length,
    }));
  });

  readonly distributionMax = computed(() => {
    const max = Math.max(...this.distribution().map((b) => b.count), 0);
    return max === 0 ? 1 : max;
  });

  readonly totalGains = computed(() =>
    this.cards().reduce((s, c) => s + c.contribution, 0),
  );
  readonly totalLosses = computed(() =>
    this.cards().reduce((s, c) => s + c.losses, 0),
  );
  readonly netResult = computed(() => this.totalGains() - this.totalLosses());

  readonly pnl = computed(() =>
    [...this.cards()]
      .map((c) => ({
        id: c.id,
        fullName: c.fullName,
        gains: c.contribution,
        losses: c.losses,
        net: c.contribution - c.losses,
      }))
      .sort((a, b) => b.net - a.net),
  );

  readonly pnlMax = computed(() => {
    const max = Math.max(
      ...this.pnl().map((r) => r.gains),
      ...this.pnl().map((r) => r.losses),
      0,
    );
    return max === 0 ? 1 : max;
  });

  constructor() {
    this.supervisorsService.list().subscribe({
      next: (data) => {
        this.cards.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message ?? 'No se pudieron cargar los supervisores');
        this.loading.set(false);
      },
    });
  }

  joinedBarWidth(count: number): number {
    return (count / this.joinedMax()) * 100;
  }

  contributionBarWidth(value: number): number {
    return (value / this.contributionMax()) * 100;
  }

  distributionBarHeight(count: number): number {
    return (count / this.distributionMax()) * 100;
  }

  pnlBarWidth(amount: number): number {
    return (amount / this.pnlMax()) * 100;
  }

  toneClass(tone: DistributionTone): string {
    if (tone === 'empty') return 'bg-color3';
    if (tone === 'excess') return 'bg-color2';
    return 'bg-color4';
  }
}
