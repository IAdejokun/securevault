import { Component, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { NgClass } from '@angular/common';
import { AuthService } from '../../core/services/auth';
import { DemoService } from '../../core/services/demo';

interface DemoResult {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: any;
  errorMessage: string;
}

@Component({
  selector: 'app-playground',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './playground.html',
  styleUrl: './playground.css',
})
export class PlaygroundComponent {
  publicKey = '';
  authKey = '';
  privKey = '';

  publicResult: DemoResult = { status: 'idle', data: null, errorMessage: '' };
  authResult: DemoResult = { status: 'idle', data: null, errorMessage: '' };
  privResult: DemoResult = { status: 'idle', data: null, errorMessage: '' };

  constructor(
    private demo: DemoService,
    private auth: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  testPublic() {
    if (!this.publicKey.trim()) {
      this.publicResult = { status: 'error', data: null, errorMessage: 'Paste a key first.' };
      return;
    }
    this.publicResult = { status: 'loading', data: null, errorMessage: '' };
    this.cdr.detectChanges();
    this.demo.callPublic(this.publicKey.trim()).subscribe({
      next: (data) => {
        this.publicResult = { status: 'success', data, errorMessage: '' };
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.publicResult = {
          status: 'error',
          data: null,
          errorMessage: err.error?.detail ?? 'Request failed',
        };
        this.cdr.detectChanges();
      },
    });
  }

  testAuth() {
    if (!this.authKey.trim()) {
      this.authResult = { status: 'error', data: null, errorMessage: 'Paste a key first.' };
      return;
    }
    this.authResult = { status: 'loading', data: null, errorMessage: '' };
    this.cdr.detectChanges();
    this.demo.callAuthenticated(this.authKey.trim()).subscribe({
      next: (data) => {
        this.authResult = { status: 'success', data, errorMessage: '' };
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.authResult = {
          status: 'error',
          data: null,
          errorMessage: err.error?.detail ?? 'Request failed',
        };
        this.cdr.detectChanges();
      },
    });
  }

  testPriv() {
    if (!this.privKey.trim()) {
      this.privResult = { status: 'error', data: null, errorMessage: 'Paste a key first.' };
      return;
    }
    this.privResult = { status: 'loading', data: null, errorMessage: '' };
    this.cdr.detectChanges();
    this.demo.callPrivileged(this.privKey.trim()).subscribe({
      next: (data) => {
        this.privResult = { status: 'success', data, errorMessage: '' };
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.privResult = {
          status: 'error',
          data: null,
          errorMessage: err.error?.detail ?? 'Request failed',
        };
        this.cdr.detectChanges();
      },
    });
  }

  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  logout() {
    this.auth.logout();
  }

  prettyPrint(data: any): string {
    return JSON.stringify(data, null, 2);
  }
}
