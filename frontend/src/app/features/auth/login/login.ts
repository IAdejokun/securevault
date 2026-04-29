import { Component, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent {
  email = '';
  password = '';
  error = '';
  loading = false;

  constructor(
    private auth: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  submit() {
    this.error = '';

    if (!this.email.trim()) {
      this.error = 'Email is required.';
      return;
    }
    if (!this.email.includes('@')) {
      this.error = 'Please enter a valid email address.';
      return;
    }
    if (!this.password.trim()) {
      this.error = 'Password is required.';
      return;
    }

    this.loading = true;
    this.cdr.detectChanges();

    this.auth.login({ email: this.email, password: this.password }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;

        if (err.status === 401) {
          this.error = 'Invalid email or password.';
        } else if (err.status === 0) {
          this.error = 'Cannot reach the server. Is the backend running?';
        } else if (typeof err.error?.detail === 'string') {
          this.error = err.error.detail;
        } else {
          this.error = 'Login failed. Please try again.';
        }

        this.cdr.detectChanges();
      },
    });
  }
}
