import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { map } from 'rxjs';

import {
  AgentCard,
  ClaimCase,
  ClaimCaseStatus,
  ClientCard,
  SupervisorCard,
} from '../../../core/models';
import { AgentsService } from '../agents.service';
import { ClientsService } from '../../clients/clients.service';
import { SupervisorsService } from '../../supervisors/supervisors.service';
import { MOCK_CLAIM_CASES } from '../../claims/mock-claim-cases';

@Component({
  selector: 'app-agent-detail',
  imports: [RouterLink, CurrencyPipe, ReactiveFormsModule],
  templateUrl: './agent-detail.html',
})
export class AgentDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly agentsService = inject(AgentsService);
  private readonly clientsService = inject(ClientsService);
  private readonly supervisorsService = inject(SupervisorsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly routeId = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: NaN },
  );

  readonly agent = signal<AgentCard | null>(null);
  readonly clients = signal<ClientCard[]>([]);
  readonly supervisors = signal<SupervisorCard[]>([]);
  readonly loading = signal(true);
  readonly notFound = signal(false);
  readonly editing = signal(false);
  readonly saving = signal(false);

  readonly form = this.fb.group({
    fullName: ['', Validators.required],
    status: this.fb.control<'active' | 'inactive'>('active'),
    supervisorId: [1, Validators.required],
    contribution: [0, [Validators.required, Validators.min(0)]],
    losses: [0, [Validators.required, Validators.min(0)]],
    photoUrl: ['', Validators.required],
  });

  readonly assignedClients = computed(() => {
    const a = this.agent();
    if (!a) return [];
    return this.clients()
      .filter((c) => c.agentId === a.id)
      .sort((x, y) => x.lastName.localeCompare(y.lastName));
  });

  readonly assignedClaims = computed<ClaimCase[]>(() => {
    const userIds = new Set(this.assignedClients().map((c) => c.userId));
    return MOCK_CLAIM_CASES.filter((c) => userIds.has(c.userId));
  });

  readonly supervisor = computed(() => {
    const a = this.agent();
    if (!a) return null;
    return this.supervisors().find((s) => s.id === a.supervisorId) ?? null;
  });

  readonly net = computed(() => {
    const a = this.agent();
    if (!a) return 0;
    return a.contribution - a.losses;
  });

  constructor() {
    const id = this.routeId();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      this.loading.set(false);
      return;
    }

    this.agentsService.list().subscribe({
      next: (data) => {
        const found = data.find((a) => a.id === id);
        if (!found) {
          this.notFound.set(true);
        } else {
          this.agent.set(found);
        }
        this.loading.set(false);
      },
      error: () => {
        this.notFound.set(true);
        this.loading.set(false);
      },
    });

    this.clientsService.list().subscribe({
      next: (data) => this.clients.set(data),
      error: () => undefined,
    });
    this.supervisorsService.list().subscribe({
      next: (data) => this.supervisors.set(data),
      error: () => undefined,
    });
  }

  startEdit(): void {
    const a = this.agent();
    if (!a) return;
    this.form.reset({
      fullName: a.fullName,
      status: a.status,
      supervisorId: a.supervisorId,
      contribution: a.contribution,
      losses: a.losses,
      photoUrl: a.photoUrl,
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
    const a = this.agent();
    if (!a) return;
    this.saving.set(true);
    this.agentsService.update(a.id, this.form.getRawValue()).subscribe({
      next: (updated) => {
        this.agent.set(updated);
        this.editing.set(false);
        this.saving.set(false);
      },
      error: () => {
        this.saving.set(false);
      },
    });
  }

  objectLabel(obj: string): string {
    return obj === 'car' ? 'Auto' : obj === 'laptop' ? 'Laptop' : 'Paquete';
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
}
