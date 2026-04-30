import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface SystemStats {
  total_users: number;
  total_keys: number;
  active_keys: number;
  events_24h: number;
  replay_attempts: number;
  failed_logins_24h: number;
}

export interface EventTypeCount {
  event_type: string;
  count: number;
}

export interface AdminEvent {
  id: string;
  event_type: string;
  zone: string;
  ip_address: string | null;
  user_id: string | null;
  anomaly_score: number | null;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private base = environment.apiUrl + '/admin';

  constructor(private http: HttpClient) {}

  getStats(): Observable<SystemStats> {
    return this.http.get<SystemStats>(`${this.base}/stats`);
  }

  getEventsByType(): Observable<EventTypeCount[]> {
    return this.http.get<EventTypeCount[]>(`${this.base}/events-by-type`);
  }

  getRecentEvents(): Observable<AdminEvent[]> {
    return this.http.get<AdminEvent[]>(`${this.base}/recent-events?limit=50`);
  }
}
