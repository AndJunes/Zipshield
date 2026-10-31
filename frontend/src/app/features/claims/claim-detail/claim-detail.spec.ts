import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of, Subject } from 'rxjs';

import { ClaimDetail } from './claim-detail';
import { ClaimsService } from '../claims.service';
import { PoliciesService } from '../../policies/policies.service';
import { ClientsService } from '../../clients/clients.service';
import { ClaimCase } from '../../../core/models';

function baseClaim(overrides: Partial<ClaimCase> = {}): ClaimCase {
  return {
    id: 1,
    userId: 'user_001',
    object: 'car',
    conversation: 'Cliente: choqué el auto',
    imageUrls: ['http://img.test/1.jpg'],
    evidenceStandardMet: true,
    evidenceStandardMetReason: 'ok',
    riskFlags: ['none'],
    issueType: 'dent',
    objectPart: 'door',
    claimStatus: 'supported',
    claimStatusJustification: 'Evidencia suficiente',
    supportingImageIds: ['img_1'],
    validImage: true,
    severity: 'low',
    policyId: null,
    dateOfLoss: null,
    ...overrides,
  };
}

describe('ClaimDetail — edit vs. analyze race', () => {
  let analyzeSubject: Subject<ClaimCase>;
  let claimsServiceMock: Partial<ClaimsService>;

  beforeEach(async () => {
    analyzeSubject = new Subject<ClaimCase>();
    claimsServiceMock = {
      getById: () => of(baseClaim()),
      analyze: () => analyzeSubject.asObservable(),
      update: (_id: number, changes: Partial<ClaimCase>) =>
        of({ ...baseClaim(), ...changes } as ClaimCase),
    };

    await TestBed.configureTestingModule({
      imports: [ClaimDetail],
      providers: [
        { provide: ClaimsService, useValue: claimsServiceMock },
        { provide: PoliciesService, useValue: { getById: () => of(null) } },
        { provide: ClientsService, useValue: { list: () => of([]) } },
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of(convertToParamMap({ id: '1' })) },
        },
      ],
    }).compileComponents();
  });

  it('disables the "Editar" button while the analysis is running', () => {
    const fixture = TestBed.createComponent(ClaimDetail);
    fixture.detectChanges();

    fixture.componentInstance.analyze();
    fixture.detectChanges();

    const buttons = fixture.nativeElement.querySelectorAll('button');
    const editButton = Array.from(buttons as NodeListOf<HTMLButtonElement>).find(
      (b) => b.textContent?.trim() === 'Editar',
    );
    expect(editButton?.disabled).toBe(true);
  });

  it('does not silently overwrite the analysis result when it arrives mid-edit', () => {
    const fixture = TestBed.createComponent(ClaimDetail);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.analyze();
    component.startEdit(); // the user managed to start editing before it resolved

    const analyzed = baseClaim({ claimStatusJustification: 'Analizado por IA', severity: 'high' });
    analyzeSubject.next(analyzed);
    analyzeSubject.complete();

    expect(component.claim()?.claimStatusJustification).not.toBe('Analizado por IA');
    expect(component.pendingAnalysisResult()).toEqual(analyzed);

    component.cancelEdit();
    expect(component.claim()).toEqual(analyzed);
    expect(component.pendingAnalysisResult()).toBeNull();
  });

  it('applies the analysis normally when NOT editing', () => {
    const fixture = TestBed.createComponent(ClaimDetail);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.analyze();
    const analyzed = baseClaim({ claimStatusJustification: 'Analizado por IA' });
    analyzeSubject.next(analyzed);
    analyzeSubject.complete();

    expect(component.claim()?.claimStatusJustification).toBe('Analizado por IA');
    expect(component.pendingAnalysisResult()).toBeNull();
  });
});
