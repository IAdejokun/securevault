import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { NgClass, DatePipe } from '@angular/common';
import { AuthService } from '../../core/services/auth';
import { ApiKeyService } from '../../core/services/api-key';
import { ApiKeyResponse, ApiKeyCreateResponse } from '../../core/models/api-key.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [FormsModule, NgClass, DatePipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent implements OnInit {
  keys: ApiKeyResponse[] = [];
  loading = true;
  error = '';

  showCreateForm = false;
  newKeyName = '';
  newKeyZone = 'authenticated';
  creating = false;
  createError = '';

  createdKey: ApiKeyCreateResponse | null = null;
  rawKeyCopied = false;

  isAdmin = false;

  constructor(
    private keyService: ApiKeyService,
    private auth: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit() {
    this.loadKeys();

    this.auth.me().subscribe({
      next: (user: any) => {
        this.isAdmin = !!user.is_admin;
        this.cdr.detectChanges();
      },
    });
  }

  goToAdmin() {
    this.router.navigate(['/admin']);
  }

  loadKeys() {
    this.loading = true;
    this.error = '';
    this.cdr.detectChanges();

    this.keyService.listKeys().subscribe({
      next: (keys) => {
        this.keys = keys;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load keys.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  createKey() {
    if (!this.newKeyName.trim()) {
      this.createError = 'Key name is required.';
      this.cdr.detectChanges();
      return;
    }
    this.creating = true;
    this.createError = '';
    this.cdr.detectChanges();

    this.keyService
      .createKey({
        name: this.newKeyName.trim(),
        zone: this.newKeyZone,
      })
      .subscribe({
        next: (res) => {
          this.createdKey = res;
          this.showCreateForm = false;
          this.newKeyName = '';
          this.newKeyZone = 'authenticated';
          this.creating = false;
          this.cdr.detectChanges();
          this.loadKeys();
        },
        error: (err) => {
          this.createError = err.error?.detail ?? 'Failed to create key.';
          this.creating = false;
          this.cdr.detectChanges();
        },
      });
  }

  copyRawKey() {
    if (this.createdKey) {
      navigator.clipboard.writeText(this.createdKey.raw_key);
      this.rawKeyCopied = true;
      this.cdr.detectChanges();
      setTimeout(() => {
        this.rawKeyCopied = false;
        this.cdr.detectChanges();
      }, 2000);
    }
  }

  dismissCreatedKey() {
    this.createdKey = null;
    this.cdr.detectChanges();
  }

  goToKey(id: string) {
    this.router.navigate(['/keys', id]);
  }

  logout() {
    this.auth.logout();
  }

  zoneBadgeClass(zone: string): string {
    const map: Record<string, string> = {
      public: 'badge-public',
      authenticated: 'badge-auth',
      privileged: 'badge-priv',
    };
    return map[zone] ?? 'badge-auth';
  }
}
