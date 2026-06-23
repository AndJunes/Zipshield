import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AgentCard, ClientCard } from '../../../core/models';
import { AgentsService } from '../../agents/agents.service';
import { ClientsService } from '../clients.service';
import { MOCK_CLAIM_CASES } from '../../claims/mock-claim-cases';

type StatusFilter = 'all' | 'active' | 'inactive' | 'risk';
type ClaimsFilter = 'all' | 'with' | 'without';

@Component({
  selector: 'app-clients-details',
  imports: [RouterLink, ReactiveFormsModule],
  templateUrl: './clients-details.html',
})
export class ClientsDetails {
  private readonly clientsService = inject(ClientsService);
  private readonly agentsService = inject(AgentsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly userIdsWithClaims = new Set(
    MOCK_CLAIM_CASES.map((c) => c.userId),
  );

  readonly clients = signal<ClientCard[]>([]);
  readonly agents = signal<AgentCard[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly statusFilter = signal<StatusFilter>('all');
  readonly claimsFilter = signal<ClaimsFilter>('all');
  readonly creating = signal(false);
  readonly saving = signal(false);

  readonly createForm = this.fb.group({
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

  readonly totalCount = computed(() => this.clients().length);

  readonly filtered = computed(() => {
    const status = this.statusFilter();
    const claims = this.claimsFilter();
    return this.clients().filter((c) => {
      if (status === 'active' && c.status !== 'active') return false;
      if (status === 'inactive' && c.status !== 'inactive') return false;
      if (status === 'risk' && c.history.historyFlags.length === 0) return false;

      if (claims === 'with' && !this.userIdsWithClaims.has(c.userId)) return false;
      if (claims === 'without' && this.userIdsWithClaims.has(c.userId)) return false;

      return true;
    });
  });

  readonly statusFilters: { label: string; value: StatusFilter }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Activos', value: 'active' },
    { label: 'Inactivos', value: 'inactive' },
    { label: 'Con riesgo', value: 'risk' },
  ];

  readonly claimsFilters: { label: string; value: ClaimsFilter }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Con reclamos', value: 'with' },
    { label: 'Sin reclamos', value: 'without' },
  ];

  constructor() {
    this.load();
    this.agentsService.list().subscribe({
      next: (data) => this.agents.set(data),
      error: () => undefined,
    });
  }

  private load(): void {
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
  }

  agentName(agentId: number): string {
    return this.agents().find((a) => a.id === agentId)?.fullName ?? '—';
  }

  hasClaims(userId: string): boolean {
    return this.userIdsWithClaims.has(userId);
  }

  setStatusFilter(value: StatusFilter): void {
    this.statusFilter.set(value);
  }

  setClaimsFilter(value: ClaimsFilter): void {
    this.claimsFilter.set(value);
  }

  startCreate(): void {
    const nextIdGuess = this.clients().length + 1;
    this.createForm.reset({
      firstName: '',
      lastName: '',
      email: '',
      phone: null,
      city: null,
      clientNumber: `CL-${String(nextIdGuess).padStart(3, '0')}`,
      status: 'active',
      agentId: this.agents()[0]?.id ?? 1,
      photoUrl: `https://i.pravatar.cc/300?u=client-new-${Date.now()}`,
    });
    this.creating.set(true);
  }

  cancelCreate(): void {
    this.creating.set(false);
  }

  saveCreate(): void {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.clientsService.create(this.createForm.getRawValue()).subscribe({
      next: () => {
        this.creating.set(false);
        this.saving.set(false);
        this.load();
      },
      error: () => this.saving.set(false),
    });
  }

  filterChipClass(active: boolean): string {
    return active
      ? 'bg-color2 text-color5 border-color2'
      : 'bg-white text-color2 border-color3/30 hover:bg-color4/20 hover:border-color4';
  }
}
