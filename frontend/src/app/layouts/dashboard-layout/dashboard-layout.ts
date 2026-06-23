import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Sidebar } from './sidebar/sidebar';
import { UserMenu } from '../../shared/components/user-menu/user-menu';

@Component({
  selector: 'app-dashboard-layout',
  imports: [RouterOutlet, Sidebar, UserMenu],
  templateUrl: './dashboard-layout.html',
  styleUrl: './dashboard-layout.css',
})
export class DashboardLayout {}
