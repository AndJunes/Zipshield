import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { map } from 'rxjs';

import { AgentCard, SupervisorCard } from '../../../core/models';
import { SupervisorsService } from '../supervisors.service';
import { AgentsService } from '../../agents/agents.service';

@Component({
  selector: 'app-supervisor-detail',
  imports: [RouterLink, CurrencyPipe, ReactiveFormsModule],
  templateUrl: './supervisor-detail.html',
})
export class SupervisorDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly supervisorsService = inject(SupervisorsService);
  private readonly agentsService = inject(AgentsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly routeId = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: NaN },
  );

  readonly supervisor = signal<SupervisorCard | null>(null);
  readonly agents = signal<AgentCard[]>([]);
  readonly loading = signal(true);
  readonly notFound = signal(false);
  readonly editing = signal(false);
  readonly saving = signal(false);

  readonly form = this.fb.group({
    fullName: ['', Validators.required],
    status: this.fb.control<'active' | 'inactive'>('active'),
    contribution: [0, [Validators.required, Validators.min(0)]],
    losses: [0, [Validators.required, Validators.min(0)]],
    photoUrl: ['', Validators.required],
  });

  readonly assignedAgents = computed(() => {
    const s = this.supervisor();
    if (!s) return [];
    return this.agents()
      .filter((a) => a.supervisorId === s.id)
      .sort((a, b) => b.contribution - a.contribution);
  });

  readonly totalClients = computed(() =>
    this.assignedAgents().reduce((sum, a) => sum + a.clientCount, 0),
  );

  readonly totalClaims = computed(() =>
    this.assignedAgents().reduce(
      (sum, a) => sum + a.claims.resolved + a.claims.inProgress,
      0,
    ),
  );

  readonly net = computed(() => {
    const s = this.supervisor();
    if (!s) return 0;
    return s.contribution - s.losses;
  });

  constructor() {
    const id = this.routeId();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      this.loading.set(false);
      return;
    }

    this.supervisorsService.list().subscribe({
      next: (data) => {
        const found = data.find((s) => s.id === id);
        if (!found) {
          this.notFound.set(true);
        } else {
          this.supervisor.set(found);
        }
        this.loading.set(false);
      },
      error: () => {
        this.notFound.set(true);
        this.loading.set(false);
      },
    });

    this.agentsService.list().subscribe({
      next: (data) => this.agents.set(data),
      error: () => undefined,
    });
  }

  startEdit(): void {
    const s = this.supervisor();
    if (!s) return;
    this.form.reset({
      fullName: s.fullName,
      status: s.status,
      contribution: s.contribution,
      losses: s.losses,
      photoUrl: s.photoUrl,
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
    const s = this.supervisor();
    if (!s) return;
    this.saving.set(true);
    this.supervisorsService.update(s.id, this.form.getRawValue()).subscribe({
      next: (updated) => {
        this.supervisor.set(updated);
        this.editing.set(false);
        this.saving.set(false);
      },
      error: () => this.saving.set(false),
    });
  }
}
