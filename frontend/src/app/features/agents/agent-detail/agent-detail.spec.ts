import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of } from 'rxjs';

import { AgentDetail } from './agent-detail';
import { AgentsService } from '../agents.service';
import { ClientsService } from '../../clients/clients.service';
import { SupervisorsService } from '../../supervisors/supervisors.service';
import { ClaimsService } from '../../claims/claims.service';
import { AgentCard, ClaimCase, ClientCard } from '../../../core/models';

function fakeAgent(overrides: Partial<AgentCard> = {}): AgentCard {
  return {
    id: 1,
    fullName: 'Juan Ruiz',
    status: 'active',
    contribution: 0,
    losses: 0,
    photoUrl: 'x',
    createdAt: '2026-01-01',
    supervisorId: 1,
    clientCount: 1,
    claims: { resolved: 0, inProgress: 0, granted: 0, rejected: 0 },
    ...overrides,
  };
}

function fakeClient(agentId: number, userId: string): ClientCard {
  return {
    id: 1,
    userId,
    firstName: 'Ana',
    lastName: 'Pérez',
    email: 'ana@example.com',
    phone: null,
    city: null,
    clientNumber: 'CL-001',
    status: 'active',
    agentId,
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
    policyId: null,
    dateOfLoss: null,
  };
}

describe('AgentDetail — BUG-10: reclamos reales, no mock', () => {
  it('deriva assignedClaims de ClaimsService.list() para los clientes del agente', async () => {
    const client = fakeClient(1, 'user_001');
    const claim = fakeClaim('user_001');

    await TestBed.configureTestingModule({
      imports: [AgentDetail],
      providers: [
        { provide: AgentsService, useValue: { list: () => of([fakeAgent()]) } },
        { provide: ClientsService, useValue: { list: () => of([client]) } },
        { provide: SupervisorsService, useValue: { list: () => of([]) } },
        { provide: ClaimsService, useValue: { list: () => of([claim]) } },
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of(convertToParamMap({ id: '1' })) },
        },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(AgentDetail);
    fixture.detectChanges();

    expect(fixture.componentInstance.assignedClaims()).toEqual([claim]);
  });
});
