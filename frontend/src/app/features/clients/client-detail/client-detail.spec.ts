import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of } from 'rxjs';

import { ClientDetail } from './client-detail';
import { ClientsService } from '../clients.service';
import { AgentsService } from '../../agents/agents.service';
import { ClaimsService } from '../../claims/claims.service';
import { ClaimCase, ClientCard } from '../../../core/models';

function fakeClient(overrides: Partial<ClientCard> = {}): ClientCard {
  return {
    id: 1,
    userId: 'user_001',
    firstName: 'Ana',
    lastName: 'Pérez',
    email: 'ana@example.com',
    phone: null,
    city: null,
    clientNumber: 'CL-001',
    status: 'active',
    agentId: 1,
    photoUrl: 'x',
    history: {
      pastClaimCount: 0,
      acceptClaim: 0,
      manualReviewClaim: 0,
      rejectedClaim: 0,
      last90DaysClaimCount: 0,
      historyFlags: [],
      historySummary: '',
    },
    ...overrides,
  };
}

function fakeClaim(userId: string): ClaimCase {
  return {
    id: 1,
    userId,
    object: 'car',
    conversation: '',
    imageUrls: [],
    evidenceStandardMet: true,
    evidenceStandardMetReason: '',
    riskFlags: ['none'],
    issueType: 'unknown',
    objectPart: 'unknown',
    claimStatus: 'supported',
    claimStatusJustification: '',
    supportingImageIds: [],
    validImage: true,
    severity: 'unknown',
    analysisStatus: 'none',
    policyId: null,
    dateOfLoss: null,
  };
}

describe('ClientDetail — real claims, not mock data', () => {
  it('derives clientClaims from ClaimsService.list(), not hardcoded data', async () => {
    const realClaim = fakeClaim('user_001');

    await TestBed.configureTestingModule({
      imports: [ClientDetail],
      providers: [
        { provide: ClientsService, useValue: { getById: () => of(fakeClient()) } },
        { provide: AgentsService, useValue: { list: () => of([]) } },
        { provide: ClaimsService, useValue: { list: () => of([realClaim]) } },
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of(convertToParamMap({ id: '1' })) },
        },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(ClientDetail);
    fixture.detectChanges();

    expect(fixture.componentInstance.clientClaims()).toEqual([realClaim]);
  });

  it('does not show another user\'s claims', async () => {
    const claimOfSomeoneElse = fakeClaim('user_999');

    await TestBed.configureTestingModule({
      imports: [ClientDetail],
      providers: [
        { provide: ClientsService, useValue: { getById: () => of(fakeClient()) } },
        { provide: AgentsService, useValue: { list: () => of([]) } },
        { provide: ClaimsService, useValue: { list: () => of([claimOfSomeoneElse]) } },
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of(convertToParamMap({ id: '1' })) },
        },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(ClientDetail);
    fixture.detectChanges();

    expect(fixture.componentInstance.clientClaims()).toEqual([]);
  });
});
