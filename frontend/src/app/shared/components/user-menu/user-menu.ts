import { Component, ElementRef, HostListener, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-user-menu',
  imports: [RouterLink],
  templateUrl: './user-menu.html',
})
export class UserMenu {
  private readonly authService = inject(AuthService);
  private readonly host = inject(ElementRef<HTMLElement>);

  readonly user = this.authService.currentUser;
  readonly open = signal(false);

  toggle(): void {
    this.open.update((v) => !v);
  }

  close(): void {
    this.open.set(false);
  }

  roleLabel(role: string): string {
    if (role === 'admin') return 'Administrador';
    if (role === 'supervisor') return 'Supervisor';
    if (role === 'agent') return 'Agente';
    if (role === 'client') return 'Cliente';
    return role;
  }

  logout(): void {
    this.close();
    this.authService.logout();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.host.nativeElement.contains(event.target as Node)) {
      this.close();
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.close();
  }
}
