export type RetentionStatus =
  | "none"
  | "to_contact"
  | "contacted"
  | "retained"
  | "ignored";

export type ActionType = "call" | "email" | "discount" | "onboarding" | "other";

export type ActionStatus = "todo" | "in_progress" | "done" | "cancelled";

export interface SuggestedAction {
  action_type: ActionType;
  label: string;
  feature: string | null;
  impact: number;
}

export interface CustomerAction {
  id: number;
  customer_id: number;
  created_by_user_id: number | null;
  action_type: ActionType;
  status: ActionStatus;
  note: string | null;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerActionPayload {
  action_type: ActionType;
  status?: ActionStatus;
  note?: string | null;
  due_date?: string | null;
}

export interface CustomerActionUpdatePayload {
  action_type?: ActionType;
  status?: ActionStatus;
  note?: string | null;
  due_date?: string | null;
}

export interface RetentionUpdatePayload {
  retention_status?: RetentionStatus;
  owner_user_id?: number | null;
}

export interface RetentionUpdateResponse {
  customer_id: number;
  external_id: string;
  name: string | null;
  retention_status: RetentionStatus;
  owner_user_id: number | null;
}

export interface ActionFilters {
  status?: ActionStatus;
  owner?: number;
  overdue?: boolean;
}

/** Membre de l'organisation, tel que renvoyé par GET /users. */
export interface RetentionUser {
  id: number;
  full_name: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
  is_active: boolean;
}
