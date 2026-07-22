import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { PoliciesDetails } from './policies-details';
import { PoliciesService } from '../policies.service';
import { ClientsService } from '../../clients/clients.service';

describe('PoliciesDetails — A9/A10: validación de cliente y errores visibles', () => {
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

  it('A9: el formulario es inválido con clientId=0 (ningún cliente elegido)', async () => {
    const component = await setup({ list: () => of([]) });
    component.startCreate();
    component.createForm.patchValue({ clientId: 0 });
    expect(component.createForm.invalid).toBe(true);
  });

  it('A9: el formulario es válido con un clientId real', async () => {
    const component = await setup({ list: () => of([]) });
    component.startCreate();
    component.createForm.patchValue({
      clientId: 5,
      name: 'Póliza X',
      effectiveDate: '2026-01-01',
    });
    expect(component.createForm.valid).toBe(true);
  });

  it('A10: doQuote() muestra un mensaje de error cuando la petición falla', async () => {
    const component = await setup({
      list: () => of([]),
      quote: () => throwError(() => new Error('boom')),
    });
    component.startCreate();
    component.doQuote();
    expect(component.quoteError()).toBeTruthy();
    expect(component.quoting()).toBe(false);
  });

  it('A10: saveCreate() muestra un mensaje de error cuando la petición falla', async () => {
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

describe('PoliciesDetails — A12: fecha por defecto en zona horaria local, no UTC', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('startCreate() precarga la fecha de HOY en hora local, no la de mañana en UTC', async () => {
    // 23:00 en America/Mexico_City (UTC-6) ya es "mañana" en UTC — exactamente el
    // escenario que `toISOString().slice(0, 10)` calculaba mal.
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
