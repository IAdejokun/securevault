import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { NgClass, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth';
import {
  AdminService,
  SystemStats,
  EventTypeCount,
  AdminEvent,
} from '../../core/services/admin';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [NgClass, DatePipe],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class AdminComponent implements OnInit, OnDestroy {
  stats: SystemStats | null = null;
  byType: EventTypeCount[] = [];
  events: AdminEvent[] = [];
  loading = true;
  error = '';
  refreshInterval?: any;

  constructor(
    private adminService: AdminService,
    private auth: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit() {
    this.loadAll();
    // auto-refresh every 30 seconds
    this.refreshInterval = setInterval(() => this.loadAll(), 30000);
  }

  ngOnDestroy() {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }

  loadAll() {
    this.adminService.getStats().subscribe({
      next: (s) => {
        this.stats = s;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        if (err.status === 403) {
          this.error = 'Admin access required.';
        } else {
          this.error = 'Failed to load admin data.';
        }
        this.loading = false;
        this.cdr.detectChanges();
      },
    });

    this.adminService.getEventsByType().subscribe({
      next: (data) => {
        this.byType = data;
        this.cdr.detectChanges();
      },
      error: () => {},
    });

    this.adminService.getRecentEvents().subscribe({
      next: (data) => {
        this.events = data;
        this.cdr.detectChanges();
      },
      error: () => {},
    });
  }

  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  logout() {
    this.auth.logout();
  }

  zoneClass(zone: string): string {
    return (
      'badge-' + (zone === 'authenticated' ? 'auth' : zone === 'privileged' ? 'priv' : 'public')
    );
  }

  eventClass(eventType: string): string {
    if (eventType.includes('replay') || eventType.includes('anomaly')) return 'event-danger';
    if (eventType.includes('failure') || eventType.includes('rejected')) return 'event-warn';
    if (eventType.includes('success') || eventType.includes('created')) return 'event-success';
    return 'event-neutral';
  }

  // bar chart width based on max count
  barWidth(count: number): string {
    const max = Math.max(...this.byType.map((b) => b.count), 1);
    return `${(count / max) * 100}%`;
  }
}
