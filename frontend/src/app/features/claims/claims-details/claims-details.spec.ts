import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { ClaimsDetails } from './claims-details';
import { ClientsService } from '../../clients/clients.service';
import { ClaimsService, ClaimInput } from '../claims.service';
import { PoliciesService } from '../../policies/policies.service';
import { ClientCard, Policy } from '../../../core/models';

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

function fakePolicy(overrides: Partial<Policy> = {}): Policy {
  return {
    id: 10,
    clientId: 1,
    type: 'car',
    name: 'Póliza test',
    status: 'in_force',
    effectiveDate: '2026-01-01',
    expirationDate: '2026-12-31',
    cancelDate: null,
    cancelReason: null,
    sumInsured: '18000.00',
    deductible: '500.00',
    netPremium: '540.00',
    taxesFees: '111.40',
    price: '651.40',
    coverage: null,
    coverages: [],
    ...overrides,
  };
}

describe('ClaimsDetails — BUG-11: vínculo reclamo↔póliza expuesto en el formulario', () => {
  it('policiesForClient filtra solo las pólizas del cliente seleccionado', async () => {
    const clientA = fakeClient({ id: 1, userId: 'user_001' });
    const clientB = fakeClient({ id: 2, userId: 'user_002', clientNumber: 'CL-002' });
    const policyOfA = fakePolicy({ id: 10, clientId: 1 });
    const policyOfB = fakePolicy({ id: 20, clientId: 2 });

    await TestBed.configureTestingModule({
      imports: [ClaimsDetails],
      providers: [
        provideRouter([]),
        { provide: ClientsService, useValue: { list: () => of([clientA, clientB]) } },
        { provide: ClaimsService, useValue: { list: () => of([]) } },
        { provide: PoliciesService, useValue: { list: () => of([policyOfA, policyOfB]) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(ClaimsDetails);
    fixture.detectChanges();

    expect(fixture.componentInstance.policiesForClient('user_001')).toEqual([policyOfA]);
    expect(fixture.componentInstance.policiesForClient('user_002')).toEqual([policyOfB]);
  });

  it('saveCreate envía policyId y dateOfLoss al servicio de reclamos', async () => {
    let captured: ClaimInput | undefined;

    await TestBed.configureTestingModule({
      imports: [ClaimsDetails],
      providers: [
        provideRouter([]),
        { provide: ClientsService, useValue: { list: () => of([fakeClient()]) } },
        {
          provide: ClaimsService,
          useValue: {
            list: () => of([]),
            create: (input: ClaimInput) => {
              captured = input;
              return of({ id: 99 });
            },
          },
        },
        { provide: PoliciesService, useValue: { list: () => of([fakePolicy()]) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(ClaimsDetails);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.createForm.setValue({
      userId: 'user_001',
      object: 'car',
      conversation: 'Customer: choqué | Agent: ok',
      imageUrls: ['http://img.test/1.jpg'],
      policyId: 10,
      dateOfLoss: '2026-03-01',
    });
    component.saveCreate();

    expect(captured?.policyId).toBe(10);
    expect(captured?.dateOfLoss).toBe('2026-03-01');
  });
});
