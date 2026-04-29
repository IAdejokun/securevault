import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { NgClass, DatePipe } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiKeyService } from '../../core/services/api-key';
import { KeyStateService } from '../../core/services/key-state';
import { ApiKeyResponse, ApiKeyCreateResponse } from '../../core/models/api-key.model';
import { AuditLogResponse } from '../../core/models/audit.model';

@Component({
  selector: 'app-key-detail',
  standalone: true,
  imports: [NgClass, DatePipe],
  templateUrl: './key-detail.html',
  styleUrl: './key-detail.css',
})
export class KeyDetailComponent implements OnInit {
  key: ApiKeyResponse | null = null;
  logs: AuditLogResponse[] = [];
  loading = true;
  error = '';

  rotatedKey: ApiKeyCreateResponse | null = null;
  rawKeyCopied = false;
  rotating = false;
  revoking = false;
  rotateError = '';
  revokeError = '';
  showRevokeConfirm = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private keyService: ApiKeyService,
    private keyState: KeyStateService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit() {
    // Subscribe to route param changes so we re-load when navigating
    // from one key to another (Angular reuses the component otherwise)
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (id) {
        this.loadKey(id);
        this.loadLogs();
      }
    });
  }

  
  loadKey(id: string) {
    console.log('=== loadKey called for id:', id);
    console.log('=== checking pending rotation BEFORE API call');
    const pendingCheck = this.keyState['_pendingRawKey'];
    console.log('=== pending raw key in service:', pendingCheck);

    this.loading = true;
    this.cdr.detectChanges();

    this.keyService.getKey(id).subscribe({
      next: (key) => {
        console.log('=== key loaded:', key.name, key.id);
        this.key = key;
        this.loading = false;

        const pending = this.keyState.consumePendingRotation();
        console.log('=== consumed pending:', pending);

        if (pending) {
          this.rotatedKey = {
            raw_key: pending.rawKey,
            name: pending.keyName,
          } as any;
          console.log('=== rotatedKey set to:', this.rotatedKey);
        }

        this.cdr.detectChanges();
        console.log('=== detectChanges called, rotatedKey is:', this.rotatedKey);
      },
      error: () => {
        this.error = 'Key not found.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  // loadKey(id: string) {
  //   this.loading = true;
  //   this.cdr.detectChanges();

  //   this.keyService.getKey(id).subscribe({
  //     next: (key) => {
  //       this.key = key;
  //       this.loading = false;

  //       // Check if we arrived here from a rotation
  //       const pending = this.keyState.consumePendingRotation();
  //       if (pending) {
  //         this.rotatedKey = {
  //           raw_key: pending.rawKey,
  //           name: pending.keyName,
  //         } as any;
  //       }

  //       this.cdr.detectChanges();
  //     },
  //     error: () => {
  //       this.error = 'Key not found.';
  //       this.loading = false;
  //       this.cdr.detectChanges();
  //     },
  //   });
  // }

  loadLogs() {
    this.keyService.getAuditLogs().subscribe({
      next: (logs) => {
        this.logs = logs;
        this.cdr.detectChanges();
      },
      error: () => {},
    });
  }

  rotate() {
    if (!this.key) return;
    this.rotating = true;
    this.rotateError = '';
    this.cdr.detectChanges();

    this.keyService.rotateKey(this.key.id).subscribe({
      next: (res) => {
        console.log('=== rotation response:', res);
        console.log('=== raw_key from response:', res.raw_key);
        this.rotating = false;
        this.keyState.setPendingRotation(res.raw_key, res.name);
        console.log('=== pending set, now navigating to /keys/' + res.id);
        this.cdr.detectChanges();
        this.router.navigate(['/keys', res.id]);
      },
      error: (err) => {
        this.rotateError = err.error?.detail ?? 'Rotation failed.';
        this.rotating = false;
        this.cdr.detectChanges();
      },
    });
  }

  // rotate() {
  //   if (!this.key) return;
  //   this.rotating = true;
  //   this.rotateError = '';
  //   this.cdr.detectChanges();

  //   this.keyService.rotateKey(this.key.id).subscribe({
  //     next: (res) => {
  //       this.rotating = false;
  //       // Store raw key in service BEFORE navigating
  //       this.keyState.setPendingRotation(res.raw_key, res.name);
  //       this.cdr.detectChanges();
  //       this.router.navigate(['/keys', res.id]);
  //     },
  //     error: (err) => {
  //       this.rotateError = err.error?.detail ?? 'Rotation failed.';
  //       this.rotating = false;
  //       this.cdr.detectChanges();
  //     },
  //   });
  // }

  confirmRevoke() {
    this.showRevokeConfirm = true;
    this.cdr.detectChanges();
  }

  revoke() {
    if (!this.key) return;
    this.revoking = true;
    this.revokeError = '';
    this.cdr.detectChanges();

    this.keyService.revokeKey(this.key.id).subscribe({
      next: () => {
        this.revoking = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.revokeError = err.error?.detail ?? 'Revocation failed.';
        this.revoking = false;
        this.showRevokeConfirm = false;
        this.cdr.detectChanges();
      },
    });
  }

  dismissRotatedKey() {
    this.rotatedKey = null;
    this.cdr.detectChanges();
  }

  copyRawKey() {
    if (this.rotatedKey) {
      navigator.clipboard.writeText(this.rotatedKey.raw_key);
      this.rawKeyCopied = true;
      this.cdr.detectChanges();
      setTimeout(() => {
        this.rawKeyCopied = false;
        this.cdr.detectChanges();
      }, 2000);
    }
  }

  back() {
    this.router.navigate(['/dashboard']);
  }

  zoneBadgeClass(zone: string): string {
    const map: Record<string, string> = {
      public: 'badge-public',
      authenticated: 'badge-auth',
      privileged: 'badge-priv',
    };
    return map[zone] ?? 'badge-auth';
  }

  eventLabel(type: string): string {
    const map: Record<string, string> = {
      'key.created': 'Created',
      'key.rotated': 'Rotated',
      'key.revoked': 'Revoked',
      'auth.login.success': 'Login',
      'auth.login.failure': 'Login failed',
      'replay.detected': 'Replay detected',
      'anomaly.flagged': 'Anomaly flagged',
    };
    return map[type] ?? type;
  }
}
