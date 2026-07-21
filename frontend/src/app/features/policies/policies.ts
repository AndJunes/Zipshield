import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Policy } from '../../core/models';
import { PoliciesService } from './policies.service';
import {
  money,
  policyStatusClass,
  policyStatusLabel,
  policyTypeLabel,
} from '../../shared/utils/policy-labels';

interface CountRow {
  key: string;
  count: number;
}

@Component({
  selector: 'app-policies',
  imports: [RouterLink],
  templateUrl: './policies.html',
})
export class Policies {
  private readonly policiesService = inject(PoliciesService);

  readonly policies = signal<Policy[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly total = computed(() => this.policies().length);
  readonly inForce = computed(
    () => this.policies().filter((p) => p.status === 'in_force').length,
  );
  readonly expiringSoon = computed(() => {
    const limit = Date.now() + 30 * 24 * 3600 * 1000;
    return this.policies().filter(
      (p) => p.status === 'in_force' && new Date(p.expirationDate).getTime() <= limit,
    ).length;
  });
  readonly premiumInForce = computed(() =>
    this.policies()
      .filter((p) => p.status === 'in_force')
      .reduce((s, p) => s + Number(p.price), 0),
  );

  readonly byStatus = computed(() => this.group(this.policies().map((p) => p.status)));
  readonly byType = computed(() => this.group(this.policies().map((p) => p.type)));
  readonly maxStatus = computed(() => Math.max(...this.byStatus().map((r) => r.count), 1));
  readonly maxType = computed(() => Math.max(...this.byType().map((r) => r.count), 1));

  constructor() {
    this.policiesService.list().subscribe({
      next: (data) => {
        this.policies.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message ?? 'No se pudieron cargar las pólizas');
        this.loading.set(false);
      },
    });
  }

  private group(values: string[]): CountRow[] {
    const counts: Record<string, number> = {};
    values.forEach((v) => {
      counts[v] = (counts[v] ?? 0) + 1;
    });
    return Object.entries(counts)
      .map(([key, count]) => ({ key, count }))
      .sort((a, b) => b.count - a.count);
  }

  statusBarWidth(count: number): number {
    return (count / this.maxStatus()) * 100;
  }

  typeBarWidth(count: number): number {
    return (count / this.maxType()) * 100;
  }

  readonly typeLabel = policyTypeLabel;
  readonly statusLabel = policyStatusLabel;
  readonly statusClass = policyStatusClass;
  readonly money = money;
}
