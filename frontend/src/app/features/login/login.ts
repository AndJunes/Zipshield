import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AuthService } from '../../core/services/auth.service';

interface DemoAccount {
  label: string;
  email: string;
  password: string;
  role: 'admin' | 'supervisor' | 'agent';
}

const slug = (s: string) =>
  s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/\s+/g, '');

function buildSupervisorAccounts(): DemoAccount[] {
  return [
    'María Fernández',
    'Carlos Méndez',
    'Sofía Ramírez',
    'Diego Salazar',
    'Lucía Vargas',
    'Andrés Cabrera',
    'Valentina Ortiz',
    'Javier Rojas',
    'Camila Torres',
    'Tomás Herrera',
  ].map((name) => {
    const [first, ...rest] = name.split(' ');
    return {
      label: name,
      email: `${slug(first)}.${slug(rest.join(''))}@zipshield.io`,
      password: 'super1234',
      role: 'supervisor' as const,
    };
  });
}

function buildAgentAccounts(): DemoAccount[] {
  return [
    'Mateo Aguirre',
    'Renata Paredes',
    'Bruno Lagos',
    'Florencia Núñez',
    'Iván Espinoza',
    'Paula Cisneros',
    'Hugo Almeida',
    'Sara Quiroga',
    'Leandro Bustos',
    'Antonella Ríos',
    'Gonzalo Pereyra',
    'Daniela Cárdenas',
  ].map((name) => {
    const [first, ...rest] = name.split(' ');
    return {
      label: name,
      email: `${slug(first)}.${slug(rest.join(''))}@zipshield.io`,
      password: 'agent1234',
      role: 'agent' as const,
    };
  });
}

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
})
export class Login {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
  });

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  readonly admin: DemoAccount = {
    label: 'Admin',
    email: 'admin@zipshield.io',
    password: 'admin1234',
    role: 'admin',
  };
  readonly supervisors = buildSupervisorAccounts();
  readonly agents = buildAgentAccounts();

  prefill(account: DemoAccount): void {
    this.form.patchValue({ email: account.email, password: account.password });
    this.error.set(null);
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.error.set(null);
    this.submitting.set(true);
    this.authService.login(this.form.getRawValue()).subscribe({
      next: () => {
        this.submitting.set(false);
        const returnUrl =
          this.route.snapshot.queryParamMap.get('returnUrl') ?? '/';
        this.router.navigateByUrl(returnUrl);
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(err?.message ?? 'No se pudo iniciar sesión');
      },
    });
  }
}
