import { CurrencyPipe } from '@angular/common';
import { Component, Input } from '@angular/core';

export interface ProfileCardData {
  id: number;
  fullName: string;
  status: 'active' | 'inactive';
  contribution: number;
  photoUrl: string;
}

@Component({
  selector: 'app-profile-card',
  imports: [CurrencyPipe],
  templateUrl: './profile-card.html',
})
export class ProfileCard {
  @Input({ required: true }) data!: ProfileCardData;
}
