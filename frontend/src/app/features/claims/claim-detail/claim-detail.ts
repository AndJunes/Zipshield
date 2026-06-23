import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { map } from 'rxjs';

import {
  ClaimCase,
  ClaimCaseStatus,
  ClaimObject,
  ClaimSeverity,
  ClientCard,
} from '../../../core/models';
import { ClientsService } from '../../clients/clients.service';
import { ClaimsService } from '../claims.service';
import { MOCK_CLAIM_CASES } from '../mock-claim-cases';
import {
  formatIssueType,
  formatObjectPart,
  formatRiskFlag,
  formatSeverity,
} from '../../../shared/utils/claim-labels';

@Component({
  selector: 'app-claim-detail',
  imports: [RouterLink, ReactiveFormsModule],
  templateUrl: './claim-detail.html',
})
export class ClaimDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly clientsService = inject(ClientsService);
  private readonly claimsService = inject(ClaimsService);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly routeId = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: NaN },
  );

  readonly claim = signal<ClaimCase | null>(null);
  readonly notFound = signal(false);
  readonly clients = signal<ClientCard[]>([]);
  readonly editing = signal(false);
  readonly saving = signal(false);

  readonly form = this.fb.group({
    object: this.fb.control<ClaimObject>('car'),
    claimStatus: this.fb.control<ClaimCaseStatus>('supported'),
    severity: this.fb.control<ClaimSeverity>('unknown'),
    evidenceStandardMet: [true],
    evidenceStandardMetReason: ['', Validators.required],
    claimStatusJustification: ['', Validators.required],
    issueType: ['', Validators.required],
    objectPart: ['', Validators.required],
    validImage: [true],
  });

  readonly client = computed(() => {
    const c = this.claim();
    if (!c) return null;
    return this.clients().find((cli) => cli.userId === c.userId) ?? null;
  });

  constructor() {
    const id = this.routeId();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      return;
    }

    const found = MOCK_CLAIM_CASES.find((c) => c.id === id);
    if (!found) {
      this.notFound.set(true);
    } else {
      this.claim.set(found);
    }

    this.clientsService.list().subscribe({
      next: (data) => this.clients.set(data),
      error: () => undefined,
    });
  }

  startEdit(): void {
    const c = this.claim();
    if (!c) return;
    this.form.reset({
      object: c.object,
      claimStatus: c.claimStatus,
      severity: c.severity,
      evidenceStandardMet: c.evidenceStandardMet,
      evidenceStandardMetReason: c.evidenceStandardMetReason,
      claimStatusJustification: c.claimStatusJustification,
      issueType: c.issueType,
      objectPart: c.objectPart,
      validImage: c.validImage,
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
    const c = this.claim();
    if (!c) return;
    this.saving.set(true);
    this.claimsService.update(c.id, this.form.getRawValue()).subscribe({
      next: (updated) => {
        this.claim.set(updated);
        this.editing.set(false);
        this.saving.set(false);
      },
      error: () => this.saving.set(false),
    });
  }

  parseConversation(raw: string): { speaker: string; text: string }[] {
    return raw.split(' | ').map((line) => {
      const idx = line.indexOf(': ');
      if (idx === -1) return { speaker: '', text: line };
      return { speaker: line.slice(0, idx).trim(), text: line.slice(idx + 2).trim() };
    });
  }

  isCustomer(speaker: string): boolean {
    const s = speaker.toLowerCase();
    return s === 'customer' || s === 'cliente';
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

  severityClass(severity: string): string {
    if (severity === 'high') return 'bg-color2 text-color5';
    if (severity === 'medium') return 'bg-color4 text-color2';
    if (severity === 'low') return 'bg-color3/30 text-color2';
    return 'bg-color5 text-color3';
  }

  readonly formatRiskFlag = formatRiskFlag;
  readonly formatIssueType = formatIssueType;
  readonly formatObjectPart = formatObjectPart;
  readonly formatSeverity = formatSeverity;
}
