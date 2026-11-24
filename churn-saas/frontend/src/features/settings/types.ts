export interface RiskSettings {
  threshold_medium: number;
  threshold_high: number;
  updated_at: string | null;
}

export interface RiskSettingsUpdate {
  threshold_medium: number;
  threshold_high: number;
}

export interface ApiKeyStatus {
  exists: boolean;
  prefix: string | null;
  created_at: string | null;
}

export interface ApiKeyRotateRead extends ApiKeyStatus {
  /** Clé en clair : renvoyée une seule fois par l'API, jamais stockée. */
  api_key: string;
}
