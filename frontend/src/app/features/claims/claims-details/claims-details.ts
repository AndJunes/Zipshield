import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  FormArray,
  FormBuilder,
  FormControl,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import {
  ClaimCase,
  ClaimCaseStatus,
  ClaimObject,
  ClientCard,
} from '../../../core/models';
import { ClientsService } from '../../clients/clients.service';
import { ClaimsService, ClaimInput } from '../claims.service';
import { formatRiskFlag } from '../../../shared/utils/claim-labels';

type ObjectFilter = ClaimObject | 'all';
type StatusFilter = ClaimCaseStatus | 'all';

@Component({
  selector: 'app-claims-details',
  imports: [RouterLink, ReactiveFormsModule],
  templateUrl: './claims-details.html',
})
export class ClaimsDetails {
  private readonly clientsService = inject(ClientsService);
  private readonly claimsService = inject(ClaimsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly cases = signal<ClaimCase[]>([]);
  readonly clients = signal<ClientCard[]>([]);
  readonly objectFilter = signal<ObjectFilter>('all');
  readonly statusFilter = signal<StatusFilter>('all');
  readonly creating = signal(false);
  readonly saving = signal(false);

  readonly createForm = this.fb.group({
    userId: ['', Validators.required],
    object: this.fb.control<ClaimObject>('car'),
    conversation: ['', Validators.required],
    imageUrls: this.fb.array<FormControl<string>>([this.fb.control('')]),
  });

  get imageUrls(): FormArray<FormControl<string>> {
    return this.createForm.controls.imageUrls;
  }

  addImage(): void {
    this.imageUrls.push(this.fb.control(''));
  }

  removeImage(index: number): void {
    this.imageUrls.removeAt(index);
    if (this.imageUrls.length === 0) {
      this.addImage();
    }
  }

  readonly filteredCases = computed(() => {
    const obj = this.objectFilter();
    const st = this.statusFilter();
    return this.cases().filter(
      (c) =>
        (obj === 'all' || c.object === obj) &&
        (st === 'all' || c.claimStatus === st),
    );
  });

  readonly objectFilters: { label: string; value: ObjectFilter }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Autos', value: 'car' },
    { label: 'Laptops', value: 'laptop' },
    { label: 'Paquetes', value: 'package' },
  ];

  readonly statusFilters: { label: string; value: StatusFilter }[] = [
    { label: 'Todos', value: 'all' },
    { label: 'Soportado', value: 'supported' },
    { label: 'Contradicho', value: 'contradicted' },
    { label: 'Sin evidencia', value: 'not_enough_information' },
  ];

  constructor() {
    this.load();
    this.clientsService.list().subscribe({
      next: (data) => this.clients.set(data),
      error: () => undefined,
    });
  }

  private load(): void {
    this.claimsService.list().subscribe({
      next: (data) => this.cases.set(data),
      error: () => undefined,
    });
  }

  clientByUserId(userId: string): ClientCard | undefined {
    return this.clients().find((c) => c.userId === userId);
  }

  setObjectFilter(value: ObjectFilter): void {
    this.objectFilter.set(value);
  }

  setStatusFilter(value: StatusFilter): void {
    this.statusFilter.set(value);
  }

  startCreate(): void {
    this.createForm.reset({
      userId: this.clients()[0]?.userId ?? '',
      object: 'car',
      conversation: 'Customer:  | Agent: ',
    });
    this.imageUrls.clear();
    this.imageUrls.push(this.fb.control(''));
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
    const raw = this.createForm.getRawValue();
    const input: ClaimInput = {
      userId: raw.userId,
      object: raw.object,
      conversation: raw.conversation,
      imageUrls: raw.imageUrls.map((u) => u.trim()).filter((u) => u.length > 0),
    };
    this.saving.set(true);
    this.claimsService.create(input).subscribe({
      next: () => {
        this.creating.set(false);
        this.saving.set(false);
        this.load();
      },
      error: () => this.saving.set(false),
    });
  }

  objectLabel(obj: ClaimObject): string {
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

  filterChipClass(active: boolean): string {
    return active
      ? 'bg-color2 text-color5 border-color2'
      : 'bg-white text-color2 border-color3/30 hover:bg-color4/20 hover:border-color4';
  }

  readonly formatRiskFlag = formatRiskFlag;
}
