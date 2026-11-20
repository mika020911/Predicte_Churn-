export interface RiskSettings {
  threshold_medium: number;
  threshold_high: number;
  updated_at: string | null;
}

export interface RiskSettingsUpdate {
  threshold_medium: number;
  threshold_high: number;
}
