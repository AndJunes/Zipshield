import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AgentCard, SupervisorCard } from '../../../core/models';
import { AgentsService } from '../agents.service';
import { SupervisorsService } from '../../supervisors/supervisors.service';

type StatusFilter = 'all' | 'active' | 'inactive';

@Component({
  selector: 'app-agents-details',
  imports: [RouterLink, CurrencyPipe, ReactiveFormsModule],
  templateUrl: './agents-details.html',
})
export class AgentsDetails {
  private readonly agentsService = inject(AgentsService);
  private readonly supervisorsService = inject(SupervisorsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly agents = signal<AgentCard[]>([]);
  readonly supervisors = signal<SupervisorCard[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly statusFilter = signal<StatusFilter>('all');
  readonly creating = signal(false);
  readonly saving = signal(false);

  readonly createForm = this.fb.group({
    fullName: ['', Validators.required],
    status: this.fb.control<'active' | 'inactive'>('active'),
    supervisorId: [1, Validators.required],
    contribution: [0, [Validators.required, Validators.min(0)]],
    losses: [0, [Validators.required, Validators.min(0)]],
    photoUrl: ['', Validators.required],
  });

  readonly sorted = computed(() =>
    [...this.agents()].sort((a, b) => b.contribution - a.contribution),
  );

  readonly filtered = computed(() => {
    const f = this.statusFilter();
    const list = this.sorted();
    if (f === 'all') return list;
    return list.filter((a) => a.status === f);
  });

  readonly filters: { label: string; value: StatusFilter }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Activos', value: 'active' },
    { label: 'Inactivos', value: 'inactive' },
  ];

  constructor() {
    this.loadAgents();
    this.supervisorsService.list().subscribe({
      next: (data) => this.supervisors.set(data),
      error: () => undefined,
    });
  }

  private loadAgents(): void {
    this.agentsService.list().subscribe({
      next: (data) => {
        this.agents.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message ?? 'No se pudieron cargar los agentes');
        this.loading.set(false);
      },
    });
  }

  setStatusFilter(value: StatusFilter): void {
    this.statusFilter.set(value);
  }

  startCreate(): void {
    const nextSeed = this.agents().length + 1;
    this.createForm.reset({
      fullName: '',
      status: 'active',
      supervisorId: this.supervisors()[0]?.id ?? 1,
      contribution: 0,
      losses: 0,
      photoUrl: `https://i.pravatar.cc/300?u=a-new-${Date.now()}`,
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
    this.agentsService.create(this.createForm.getRawValue()).subscribe({
      next: () => {
        this.creating.set(false);
        this.saving.set(false);
        this.loadAgents();
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
