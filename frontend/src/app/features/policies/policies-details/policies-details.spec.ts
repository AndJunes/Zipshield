import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { PoliciesDetails } from './policies-details';
import { PoliciesService } from '../policies.service';
import { ClientsService } from '../../clients/clients.service';

describe('PoliciesDetails — client validation and visible errors', () => {
  async function setup(policiesServiceMock: Partial<PoliciesService>) {
    await TestBed.configureTestingModule({
      imports: [PoliciesDetails],
      providers: [
        provideRouter([]),
        { provide: PoliciesService, useValue: policiesServiceMock },
        { provide: ClientsService, useValue: { list: () => of([]) } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(PoliciesDetails);
    fixture.detectChanges();
    return fixture.componentInstance;
  }

  it('marks the form invalid with clientId=0 (no client selected)', async () => {
    const component = await setup({ list: () => of([]) });
    component.startCreate();
    component.createForm.patchValue({ clientId: 0 });
    expect(component.createForm.invalid).toBe(true);
  });

  it('marks the form valid with a real clientId', async () => {
    const component = await setup({ list: () => of([]) });
    component.startCreate();
    component.createForm.patchValue({
      clientId: 5,
      name: 'Póliza X',
      effectiveDate: '2026-01-01',
    });
    expect(component.createForm.valid).toBe(true);
  });

  it('doQuote() shows an error message when the request fails', async () => {
    const component = await setup({
      list: () => of([]),
      quote: () => throwError(() => new Error('boom')),
    });
    component.startCreate();
    component.doQuote();
    expect(component.quoteError()).toBeTruthy();
    expect(component.quoting()).toBe(false);
  });

  it('saveCreate() shows an error message when the request fails', async () => {
    const component = await setup({
      list: () => of([]),
      create: () => throwError(() => new Error('boom')),
    });
    component.startCreate();
    component.createForm.patchValue({
      clientId: 5,
      name: 'Póliza X',
      effectiveDate: '2026-01-01',
    });
    component.saveCreate();
    expect(component.createError()).toBeTruthy();
    expect(component.saving()).toBe(false);
  });
});

describe('PoliciesDetails — default date in local timezone, not UTC', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('startCreate() prefills TODAY\'s date in local time, not tomorrow\'s in UTC', async () => {
    // 23:00 in America/Mexico_City (UTC-6) is already "tomorrow" in UTC — exactly the
    // scenario `toISOString().slice(0, 10)` got wrong.
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 15, 23, 0, 0));

    await TestBed.configureTestingModule({
      imports: [PoliciesDetails],
      providers: [
        provideRouter([]),
        { provide: PoliciesService, useValue: { list: () => of([]) } },
        { provide: ClientsService, useValue: { list: () => of([]) } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(PoliciesDetails);
    fixture.detectChanges();

    fixture.componentInstance.startCreate();

    expect(fixture.componentInstance.createForm.value.effectiveDate).toBe('2026-01-15');
  });
});
