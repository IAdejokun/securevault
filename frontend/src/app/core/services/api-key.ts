import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyResponse } from '../models/api-key.model';
import { AuditLogResponse } from '../models/audit.model';

@Injectable({ providedIn: 'root' })
export class ApiKeyService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  createKey(payload: ApiKeyCreateRequest): Observable<ApiKeyCreateResponse> {
    return this.http.post<ApiKeyCreateResponse>(`${this.base}/keys`, payload);
  }

  listKeys(): Observable<ApiKeyResponse[]> {
    return this.http.get<ApiKeyResponse[]>(`${this.base}/keys`);
  }

  getKey(id: string): Observable<ApiKeyResponse> {
    return this.http.get<ApiKeyResponse>(`${this.base}/keys/${id}`);
  }

  rotateKey(id: string): Observable<ApiKeyCreateResponse> {
    const nonce = crypto.randomUUID();
    const headers = new HttpHeaders({ 'X-Nonce-Token': nonce });
    return this.http.post<ApiKeyCreateResponse>(
      `${this.base}/privileged/${id}/rotate`,
      {},
      { headers },
    );
  }

  revokeKey(id: string): Observable<void> {
    const nonce = crypto.randomUUID();
    const headers = new HttpHeaders({ 'X-Nonce-Token': nonce });
    return this.http.delete<void>(`${this.base}/privileged/${id}/revoke`, { headers });
  }

  getAuditLogs(): Observable<AuditLogResponse[]> {
    return this.http.get<AuditLogResponse[]>(`${this.base}/audit`);
  }
}
