import { Component, AfterViewInit, ElementRef, ViewChildren, QueryList } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [],
  templateUrl: './landing.html',
  styleUrl: './landing.css',
})
export class LandingComponent implements AfterViewInit {
  @ViewChildren('animateOnScroll') animatedElements!: QueryList<ElementRef>;

  constructor(
    private router: Router,
    private auth: AuthService,
  ) {}

  ngAfterViewInit() {
    // Intersection observer for scroll-triggered animations
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
          }
        });
      },
      { threshold: 0.15 },
    );
    this.animatedElements.forEach((el) => observer.observe(el.nativeElement));
  }

  goToApp() {
    // If already logged in, go to dashboard; else go to register
    this.auth.isLoggedIn$
      .subscribe((loggedIn) => {
        this.router.navigate([loggedIn ? '/dashboard' : '/register']);
      })
      .unsubscribe();
  }

  goToLogin() {
    this.router.navigate(['/login']);
  }

  scrollTo(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  }
}
