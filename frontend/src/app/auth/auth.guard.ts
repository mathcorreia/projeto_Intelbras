import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isLoggedIn()) return true;

  // In dev mode (no Java backend), allow access without token
  const token = auth.getToken();
  if (token === null) {
    // No token stored — allow through in dev mode (Python ignores auth)
    return true;
  }

  router.navigate(['/login']);
  return false;
};
