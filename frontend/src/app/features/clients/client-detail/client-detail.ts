import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { map } from 'rxjs';

import {
  AgentCard,
  ClaimCase,
  ClaimCaseStatus,
  ClientCard,
} from '../../../core/models';
import { AgentsService } from '../../agents/agents.service';
import { ClientsService } from '../clients.service';
import { MOCK_CLAIM_CASES } from '../../claims/mock-claim-cases';
import {
  formatIssueType,
  formatObjectPart,
  formatRiskFlag,
  formatSeverity,
} from '../../../shared/utils/claim-labels';

@Component({
  selector: 'app-client-detail',
  imports: [RouterLink, ReactiveFormsModule],
  templateUrl: './client-detail.html',
})
export class ClientDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly clientsService = inject(ClientsService);
  private readonly agentsService = inject(AgentsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly routeId = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: NaN },
  );

  readonly client = signal<ClientCard | null>(null);
  readonly agents = signal<AgentCard[]>([]);
  readonly loading = signal(true);
  readonly notFound = signal(false);
  readonly editing = signal(false);
  readonly saving = signal(false);

  readonly form = this.fb.group({
    firstName: ['', Validators.required],
    lastName: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    phone: this.fb.control<string | null>(null),
    city: this.fb.control<string | null>(null),
    clientNumber: ['', Validators.required],
    status: this.fb.control<'active' | 'inactive'>('active'),
    agentId: [1, Validators.required],
    photoUrl: ['', Validators.required],
  });

  readonly agent = computed(() => {
    const c = this.client();
    if (!c) return null;
    return this.agents().find((a) => a.id === c.agentId) ?? null;
  });

  readonly clientClaims = computed<ClaimCase[]>(() => {
    const c = this.client();
    if (!c) return [];
    return MOCK_CLAIM_CASES.filter((claim) => claim.userId === c.userId);
  });

  constructor() {
    const id = this.routeId();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      this.loading.set(false);
      return;
    }

    this.clientsService.getById(id).subscribe((data) => {
      if (!data) {
        this.notFound.set(true);
      } else {
        this.client.set(data);
      }
      this.loading.set(false);
    });

    this.agentsService.list().subscribe({
      next: (data) => this.agents.set(data),
      error: () => undefined,
    });
  }

  startEdit(): void {
    const c = this.client();
    if (!c) return;
    this.form.reset({
      firstName: c.firstName,
      lastName: c.lastName,
      email: c.email,
      phone: c.phone,
      city: c.city,
      clientNumber: c.clientNumber,
      status: c.status,
      agentId: c.agentId,
      photoUrl: c.photoUrl,
    });
    this.editing.set(true);
  }

  cancelEdit(): void {
    this.editing.set(false);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const c = this.client();
    if (!c) return;
    this.saving.set(true);
    this.clientsService.update(c.id, this.form.getRawValue()).subscribe({
      next: (updated) => {
        this.client.set(updated);
        this.editing.set(false);
        this.saving.set(false);
      },
      error: () => this.saving.set(false),
    });
  }

  statusLabel(status: ClaimCaseStatus): string {
    if (status === 'supported') return 'Soportado';
    if (status === 'contradicted') return 'Contradicho';
    return 'Sin evidencia';
  }

  statusClass(status: ClaimCaseStatus): string {
    if (status === 'supported') return 'bg-color4 text-color2';
    if (status === 'contradicted') return 'bg-color2 text-color5';
    return 'bg-color3 text-color5';
  }

  objectLabel(obj: string): string {
    return obj === 'car' ? 'Auto' : obj === 'laptop' ? 'Laptop' : 'Paquete';
  }

  readonly formatRiskFlag = formatRiskFlag;
  readonly formatIssueType = formatIssueType;
  readonly formatObjectPart = formatObjectPart;
  readonly formatSeverity = formatSeverity;
}
