export interface AuditLogResponse {
  id: string;
  event_type: string;
  zone: string;
  ip_address: string | null;
  anomaly_score: number | null;
  meta: Record<string, any> | null;
  created_at: string;
}
