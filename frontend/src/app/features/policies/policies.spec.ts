import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { Policies } from './policies';
import { PoliciesService } from './policies.service';
import { Policy } from '../../core/models';

function fakePolicy(price: string, overrides: Partial<Policy> = {}): Policy {
  return {
    id: 1,
    clientId: 1,
    type: 'car',
    name: 'Póliza',
    status: 'in_force',
    effectiveDate: '2026-01-01',
    expirationDate: '2026-12-31',
    cancelDate: null,
    cancelReason: null,
    sumInsured: '18000.00',
    deductible: '500.00',
    netPremium: '540.00',
    taxesFees: '111.40',
    price,
    coverage: null,
    coverages: [],
    ...overrides,
  };
}

describe('Policies — premium sum without floating-point drift', () => {
  it('sums exactly 10 premiums of $0.10 with no binary rounding error', async () => {
    // Adding 0.10 ten times with JS's native `+` gives 0.9999999999999999, not 1 —
    // exactly the kind of error priceToCents (via integer cents) avoids.
    const policies = Array.from({ length: 10 }, () => fakePolicy('0.10'));

    await TestBed.configureTestingModule({
      imports: [Policies],
      providers: [
        provideRouter([]),
        { provide: PoliciesService, useValue: { list: () => of(policies) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Policies);
    fixture.detectChanges();

    expect(fixture.componentInstance.premiumInForce()).toBe(1);
  });

  it('excludes policies that are not in_force from the total', async () => {
    const policies = [fakePolicy('100.00', { status: 'in_force' }), fakePolicy('50.00', { status: 'cancelled' })];

    await TestBed.configureTestingModule({
      imports: [Policies],
      providers: [
        provideRouter([]),
        { provide: PoliciesService, useValue: { list: () => of(policies) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(Policies);
    fixture.detectChanges();

    expect(fixture.componentInstance.premiumInForce()).toBe(100);
  });
});
