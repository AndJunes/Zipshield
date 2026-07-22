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
  Policy,
} from '../../../core/models';
import { ClientsService } from '../../clients/clients.service';
import { ClaimsService } from '../claims.service';
import { PoliciesService } from '../../policies/policies.service';
import {
  formatIssueType,
  formatObjectPart,
  formatRiskFlag,
  formatSeverity,
} from '../../../shared/utils/claim-labels';
import {
  money,
  policyStatusClass,
  policyStatusLabel,
  policyTypeLabel,
} from '../../../shared/utils/policy-labels';

@Component({
  selector: 'app-claim-detail',
  imports: [RouterLink, ReactiveFormsModule],
  templateUrl: './claim-detail.html',
})
export class ClaimDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly clientsService = inject(ClientsService);
  private readonly claimsService = inject(ClaimsService);
  private readonly policiesService = inject(PoliciesService);
  private readonly fb = inject(FormBuilder).nonNullable;

  private readonly routeId = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: NaN },
  );

  readonly claim = signal<ClaimCase | null>(null);
  readonly policy = signal<Policy | null>(null);
  readonly notFound = signal(false);
  readonly clients = signal<ClientCard[]>([]);
  readonly editing = signal(false);
  readonly saving = signal(false);
  readonly saveError = signal<string | null>(null);
  readonly analyzing = signal(false);
  readonly analyzeError = signal<string | null>(null);
  readonly analyzedAt = signal<Date | null>(null);
  // BUG-09: si el análisis de IA resuelve mientras el usuario sigue editando, no se
  // pisa el resultado en silencio — se guarda aquí y se aplica al cancelar o guardar.
  readonly pendingAnalysisResult = signal<ClaimCase | null>(null);
  readonly aiModel = 'gemini-2.5-flash-lite';

  private readonly securityFlags = new Set([
    'text_instruction_present',
    'manual_review_required',
    'possible_manipulation',
  ]);

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

  readonly notAnalyzed = computed(() => {
    const c = this.claim();
    if (!c) return false;
    const reason = (c.claimStatusJustification ?? '').trim();
    return reason === '' || reason === 'Pendiente de análisis';
  });

  constructor() {
    const id = this.routeId();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      return;
    }

    this.claimsService.getById(id).subscribe({
      next: (found) => {
        if (!found) {
          this.notFound.set(true);
        } else {
          this.claim.set(found);
          if (found.policyId) {
            this.policiesService.getById(found.policyId).subscribe({
              next: (p) => this.policy.set(p),
              error: () => undefined,
            });
          }
        }
      },
      error: () => this.notFound.set(true),
    });

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
    this.applyPendingAnalysisResult();
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const c = this.claim();
    if (!c) return;
    this.saving.set(true);
    this.saveError.set(null);
    this.claimsService.update(c.id, this.form.getRawValue()).subscribe({
      next: (updated) => {
        this.claim.set(updated);
        this.editing.set(false);
        this.saving.set(false);
        // El análisis que haya llegado durante la edición ya se descartó a propósito:
        // el usuario decidió conservar y guardar su edición manual en su lugar.
        this.pendingAnalysisResult.set(null);
      },
      error: () => {
        this.saving.set(false);
        this.saveError.set('No se pudo guardar. Intentalo de nuevo.');
      },
    });
  }

  private applyPendingAnalysisResult(): void {
    const pending = this.pendingAnalysisResult();
    if (pending) {
      this.claim.set(pending);
      this.pendingAnalysisResult.set(null);
    }
  }

  analyze(): void {
    const c = this.claim();
    if (!c) return;
    this.analyzing.set(true);
    this.analyzeError.set(null);
    this.claimsService.analyze(c.id).subscribe({
      next: (updated) => {
        if (this.editing()) {
          // El usuario entró a editar mientras el análisis seguía en curso (BUG-09):
          // no se pisa el formulario en silencio. Se aplica al cancelar/guardar.
          this.pendingAnalysisResult.set(updated);
        } else {
          this.claim.set(updated);
        }
        this.analyzedAt.set(new Date());
        this.analyzing.set(false);
      },
      error: () => {
        this.analyzeError.set('No se pudo analizar. Revisá la API key o la conexión.');
        this.analyzing.set(false);
      },
    });
  }

  isSecurityFlag(flag: string): boolean {
    return this.securityFlags.has(flag);
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
  readonly policyTypeLabel = policyTypeLabel;
  readonly policyStatusLabel = policyStatusLabel;
  readonly policyStatusClass = policyStatusClass;
  readonly money = money;
}
