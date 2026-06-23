import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { SupervisorCard } from '../../../core/models';
import { SupervisorsService } from '../supervisors.service';

type StatusFilter = 'all' | 'active' | 'inactive';

@Component({
  selector: 'app-supervisors-details',
  imports: [RouterLink, CurrencyPipe, ReactiveFormsModule],
  templateUrl: './supervisors-details.html',
})
export class SupervisorsDetails {
  private readonly supervisorsService = inject(SupervisorsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly supervisors = signal<SupervisorCard[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly statusFilter = signal<StatusFilter>('all');
  readonly creating = signal(false);
  readonly saving = signal(false);

  readonly createForm = this.fb.group({
    fullName: ['', Validators.required],
    status: this.fb.control<'active' | 'inactive'>('active'),
    contribution: [0, [Validators.required, Validators.min(0)]],
    losses: [0, [Validators.required, Validators.min(0)]],
    photoUrl: ['', Validators.required],
  });

  readonly sorted = computed(() =>
    [...this.supervisors()].sort((a, b) => b.contribution - a.contribution),
  );

  readonly filtered = computed(() => {
    const f = this.statusFilter();
    const list = this.sorted();
    if (f === 'all') return list;
    return list.filter((s) => s.status === f);
  });

  readonly filters: { label: string; value: StatusFilter }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Activos', value: 'active' },
    { label: 'Inactivos', value: 'inactive' },
  ];

  constructor() {
    this.load();
  }

  private load(): void {
    this.supervisorsService.list().subscribe({
      next: (data) => {
        this.supervisors.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.message ?? 'No se pudieron cargar los supervisores');
        this.loading.set(false);
      },
    });
  }

  setStatusFilter(value: StatusFilter): void {
    this.statusFilter.set(value);
  }

  startCreate(): void {
    this.createForm.reset({
      fullName: '',
      status: 'active',
      contribution: 0,
      losses: 0,
      photoUrl: `https://i.pravatar.cc/300?u=s-new-${Date.now()}`,
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
    this.supervisorsService.create(this.createForm.getRawValue()).subscribe({
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
