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

// A11: sumar `Number(p.price)` de muchas pólizas con `+` reintroduce el error de
// redondeo binario que el resto del modelo evita a propósito manteniendo el dinero
// como string. Sumar en centavos enteros evita que el error se acumule.
function priceToCents(value: string | number): number {
  const [whole, fraction = ''] = String(value).split('.');
  const cents = (fraction + '00').slice(0, 2);
  const sign = whole.trim().startsWith('-') ? -1 : 1;
  return sign * (Math.abs(Number(whole) || 0) * 100 + Number(cents || 0));
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
  readonly premiumInForce = computed(() => {
    const totalCents = this.policies()
      .filter((p) => p.status === 'in_force')
      .reduce((cents, p) => cents + priceToCents(p.price), 0);
    return totalCents / 100;
  });

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
