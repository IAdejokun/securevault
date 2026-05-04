import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class DemoService {
  private base = environment.apiUrl + '/demo';

  constructor(private http: HttpClient) {}

  private withKey(key: string): { headers: HttpHeaders } {
    return {
      headers: new HttpHeaders({ Authorization: `Bearer ${key}` }),
    };
  }

  callPublic(key: string): Observable<any> {
    return this.http.get(`${this.base}/weather`, this.withKey(key));
  }

  callAuthenticated(key: string): Observable<any> {
    return this.http.get(`${this.base}/profile`, this.withKey(key));
  }

  callPrivileged(key: string): Observable<any> {
    return this.http.post(`${this.base}/admin/reset`, {}, this.withKey(key));
  }
}
