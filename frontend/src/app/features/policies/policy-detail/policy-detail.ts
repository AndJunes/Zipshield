import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';

import { ClaimCase, ClientCard, Policy, PolicyEvent } from '../../../core/models';
import { ClientsService } from '../../clients/clients.service';
import { ClaimsService } from '../../claims/claims.service';
import { PoliciesService } from '../policies.service';
import {
  money,
  policyEventLabel,
  policyStatusClass,
  policyStatusLabel,
  policyTypeLabel,
} from '../../../shared/utils/policy-labels';

type Tab = 'resumen' | 'coberturas' | 'historial' | 'reclamos';

const CLAIM_STATUS_LABELS: Record<string, string> = {
  supported: 'Soportado',
  contradicted: 'Contradicho',
  not_enough_information: 'Sin evidencia',
};

@Component({
  selector: 'app-policy-detail',
  imports: [RouterLink],
  templateUrl: './policy-detail.html',
})
export class PolicyDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly policiesService = inject(PoliciesService);
  private readonly clientsService = inject(ClientsService);
  private readonly claimsService = inject(ClaimsService);

  private readonly routeId = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: NaN },
  );

  readonly policy = signal<Policy | null>(null);
  readonly events = signal<PolicyEvent[]>([]);
  readonly claims = signal<ClaimCase[]>([]);
  readonly clients = signal<ClientCard[]>([]);
  readonly notFound = signal(false);
  readonly cancelling = signal(false);
  readonly tab = signal<Tab>('resumen');

  readonly client = computed(() => {
    const p = this.policy();
    if (!p) return null;
    return this.clients().find((c) => c.id === p.clientId) ?? null;
  });

  readonly canCancel = computed(() => {
    const s = this.policy()?.status;
    return s === 'in_force' || s === 'pending_cancel';
  });

  readonly tabs: { key: Tab; label: string }[] = [
    { key: 'resumen', label: 'Resumen' },
    { key: 'coberturas', label: 'Coberturas' },
    { key: 'historial', label: 'Historial' },
    { key: 'reclamos', label: 'Reclamos' },
  ];

  constructor() {
    const id = this.routeId();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      return;
    }
    this.reload(id);
    this.clientsService.list().subscribe({
      next: (data) => this.clients.set(data),
      error: () => undefined,
    });
    this.claimsService.list().subscribe({
      next: (data) => this.claims.set(data.filter((c) => c.policyId === id)),
      error: () => undefined,
    });
  }

  private reload(id: number): void {
    this.policiesService.getById(id).subscribe({
      next: (p) => this.policy.set(p),
      error: () => this.notFound.set(true),
    });
    this.policiesService.events(id).subscribe({
      next: (e) => this.events.set(e),
      error: () => undefined,
    });
  }

  setTab(t: Tab): void {
    this.tab.set(t);
  }

  cancel(): void {
    const p = this.policy();
    if (!p) return;
    this.cancelling.set(true);
    this.policiesService.cancel(p.id).subscribe({
      next: () => {
        this.cancelling.set(false);
        this.reload(p.id);
      },
      error: () => this.cancelling.set(false),
    });
  }

  claimStatusLabel(status: string): string {
    return CLAIM_STATUS_LABELS[status] ?? status;
  }

  readonly typeLabel = policyTypeLabel;
  readonly statusLabel = policyStatusLabel;
  readonly statusClass = policyStatusClass;
  readonly eventLabel = policyEventLabel;
  readonly money = money;
}
