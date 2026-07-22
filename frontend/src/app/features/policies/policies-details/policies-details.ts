import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ClientCard, Policy, PolicyQuote, PolicyStatus, PolicyType } from '../../../core/models';
import { ClientsService } from '../../clients/clients.service';
import { PoliciesService } from '../policies.service';
import {
  money,
  policyStatusClass,
  policyStatusLabel,
  policyTypeLabel,
} from '../../../shared/utils/policy-labels';

type TypeFilter = PolicyType | 'all';
type StatusFilter = PolicyStatus | 'all';

// A12: `toISOString()` convierte a UTC antes de recortar la fecha — para un usuario en
// una zona horaria negativa por la tarde/noche, esto precargaba el formulario con la
// fecha de MAÑANA en vez de la de hoy. Se arma la fecha con los componentes locales.
function todayLocalISODate(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

@Component({
  selector: 'app-policies-details',
  imports: [RouterLink, ReactiveFormsModule],
  templateUrl: './policies-details.html',
})
export class PoliciesDetails {
  private readonly policiesService = inject(PoliciesService);
  private readonly clientsService = inject(ClientsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly policies = signal<Policy[]>([]);
  readonly clients = signal<ClientCard[]>([]);
  readonly typeFilter = signal<TypeFilter>('all');
  readonly statusFilter = signal<StatusFilter>('all');
  readonly creating = signal(false);
  readonly saving = signal(false);
  readonly quote = signal<PolicyQuote | null>(null);
  readonly quoting = signal(false);
  readonly quoteError = signal<string | null>(null);
  readonly createError = signal<string | null>(null);

  readonly createForm = this.fb.group({
    // A9: Validators.required por sí solo NO rechaza 0 (solo null/vacío) — sin
    // Validators.min(1), el formulario se puede enviar con "ningún cliente elegido".
    clientId: [0, [Validators.required, Validators.min(1)]],
    type: this.fb.control<PolicyType>('car'),
    name: ['', Validators.required],
    sumInsured: [10000, [Validators.required, Validators.min(1)]],
    deductible: [0, [Validators.min(0)]],
    effectiveDate: ['', Validators.required],
    termMonths: [12, [Validators.required, Validators.min(1)]],
    coverage: this.fb.control<string | null>(null),
  });

  readonly filtered = computed(() => {
    const t = this.typeFilter();
    const s = this.statusFilter();
    return this.policies()
      .filter((p) => (t === 'all' || p.type === t) && (s === 'all' || p.status === s))
      .sort((a, b) => a.expirationDate.localeCompare(b.expirationDate));
  });

  readonly typeFilters: { label: string; value: TypeFilter }[] = [
    { label: 'Todas', value: 'all' },
    { label: 'Autos', value: 'car' },
    { label: 'Laptops', value: 'laptop' },
    { label: 'Paquetes', value: 'package' },
  ];

  readonly statusFilters: { label: string; value: StatusFilter }[] = [
    { label: 'Todas', value: 'all' },
    { label: 'Vigentes', value: 'in_force' },
    { label: 'Vencidas', value: 'expired' },
    { label: 'Canceladas', value: 'cancelled' },
  ];

  constructor() {
    this.load();
    this.clientsService.list().subscribe({
      next: (data) => this.clients.set(data),
      error: () => undefined,
    });
  }

  private load(): void {
    this.policiesService.list().subscribe({
      next: (data) => this.policies.set(data),
      error: () => undefined,
    });
  }

  clientName(id: number): string {
    const c = this.clients().find((c) => c.id === id);
    return c ? `${c.firstName} ${c.lastName}` : `#${id}`;
  }

  setTypeFilter(value: TypeFilter): void {
    this.typeFilter.set(value);
  }

  setStatusFilter(value: StatusFilter): void {
    this.statusFilter.set(value);
  }

  filterChipClass(active: boolean): string {
    return active
      ? 'bg-color2 text-color5 border-color2'
      : 'bg-white text-color2 border-color3/30 hover:bg-color4/20 hover:border-color4';
  }

  startCreate(): void {
    this.quote.set(null);
    this.quoteError.set(null);
    this.createError.set(null);
    this.createForm.reset({
      clientId: this.clients()[0]?.id ?? 0,
      type: 'car',
      name: '',
      sumInsured: 10000,
      deductible: 0,
      effectiveDate: todayLocalISODate(),
      termMonths: 12,
      coverage: null,
    });
    this.creating.set(true);
  }

  cancelCreate(): void {
    this.creating.set(false);
  }

  doQuote(): void {
    const v = this.createForm.getRawValue();
    this.quoting.set(true);
    this.quoteError.set(null);
    this.policiesService
      .quote({ type: v.type, sumInsured: v.sumInsured, clientId: v.clientId })
      .subscribe({
        next: (q) => {
          this.quote.set(q);
          this.quoting.set(false);
        },
        error: () => {
          this.quoting.set(false);
          this.quoteError.set('No se pudo cotizar. Revisá los datos e intentá de nuevo.');
        },
      });
  }

  saveCreate(): void {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.createError.set(null);
    this.policiesService.create(this.createForm.getRawValue()).subscribe({
      next: () => {
        this.creating.set(false);
        this.saving.set(false);
        this.quote.set(null);
        this.load();
      },
      error: () => {
        this.saving.set(false);
        this.createError.set('No se pudo crear la póliza. Intentá de nuevo.');
      },
    });
  }

  readonly typeLabel = policyTypeLabel;
  readonly statusLabel = policyStatusLabel;
  readonly statusClass = policyStatusClass;
  readonly money = money;
}
