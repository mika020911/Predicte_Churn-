export interface ImportAnomaly {
  row_number: number;
  external_id: string | null;
  error_type: string;
  message: string;
}

export interface ImportBatch {
  id: number;
  organization_id: number;
  uploaded_by_user_id: number;
  filename: string;
  source: string;
  status: string;
  total_rows: number;
  imported_rows: number;
  error_rows: number;
  anomaly_report: ImportAnomaly[] | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}