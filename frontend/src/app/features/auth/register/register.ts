import { Component, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class RegisterComponent {
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
    if (this.password.length < 8) {
      this.error = 'Password must be at least 8 characters.';
      return;
    }

    this.loading = true;
    this.cdr.detectChanges();

    this.auth.register({ email: this.email, password: this.password }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;

        if (err.status === 409) {
          this.error = 'An account with this email already exists.';
        } else if (err.status === 0) {
          this.error = 'Cannot reach the server. Is the backend running?';
        } else if (typeof err.error?.detail === 'string') {
          this.error = err.error.detail;
        } else {
          this.error = 'Registration failed. Please try again.';
        }

        this.cdr.detectChanges();
      },
    });
  }
}
