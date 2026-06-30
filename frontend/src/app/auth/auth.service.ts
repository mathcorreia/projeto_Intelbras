import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

const JAVA_URL = 'http://localhost:8001';
const TOKEN_KEY = 'koreon_token';

@Injectable({ providedIn: 'root' })
export class AuthService {

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${JAVA_URL}/auth/login`, { email, password }).pipe(
      tap((res: any) => {
        if (res?.token) {
          localStorage.setItem(TOKEN_KEY, res.token);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    const token = this.getToken();
    if (!token) return false;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  getCurrentUser(): { email: string; name: string; role: string; tenant_id: number } | null {
    const token = this.getToken();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        email: payload.sub,
        name: payload.name ?? payload.sub,
        role: payload.role ?? 'USER',
        tenant_id: payload.tenant_id ?? 1,
      };
    } catch {
      return null;
    }
  }
}
