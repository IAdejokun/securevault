export interface ApiKeyCreateRequest {
  name: string;
  zone: string;
  expires_at?: string | null;
}

export interface ApiKeyCreateResponse {
  id: string;
  name: string;
  prefix: string;
  last_four: string;
  zone: string;
  display_key: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  rotated_at: string | null;
  expires_at: string | null;
  raw_key: string;
}

export interface ApiKeyResponse {
  id: string;
  name: string;
  display_key: string;
  zone: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  rotated_at: string | null;
  expires_at: string | null;
}
