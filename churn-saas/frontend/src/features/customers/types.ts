import type {
    RetentionStatus,
    SuggestedAction,
} from "@/features/retention/types";

export type RiskZone = "low" | "medium" | "high";

export interface RiskReason {
    feature: string;
    impact: number;
    message: string;
}

export interface Customer {
    customer_id: number;
    external_id:string;
    name: string | null;
    email: string | null;
    score: number;
    risk_level: RiskZone;
    snapshot_date: string;
    top_reasons: RiskReason[];
    model_version: string | null;

}
export interface CustomerListResponse {
    items: Customer[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
    zone_counts: Record<RiskZone, number>;
}

export interface CustomerListParams{
    search?: string;
    zone?: RiskZone;
    page?: number;
    page_size?: number;
}

export interface CustomerObservation {
    snapshot_date: string;
    tenure_months: number;
    contract_type: number;
    mrr_change_pct: number;
    support_tickets_30d: number;
    recency_days: number;
    frequency_trend_30d: number;
    engagement_breadth: number;
    payment_failures_90d: number;
    plan_tier_rank: number;
}

export interface CustomerDetail extends Customer {
    phone_number: string | null;
    shap_values: Record<string, number>;
    observation: CustomerObservation;
    retention_status: RetentionStatus;
    owner_user_id: number | null;
    suggested_actions: SuggestedAction[];
}

export interface SimulationPayload {
    tenure_months?: number;
    contract_type?: 0 | 1;
    mrr_change_pct?: number;
    support_tickets_30d?: number;
    recency_days?: number;
    frequency_trend_30d?: number;
    engagement_breadth?: number;
    payment_failures_90d?: number;
    plan_tier_rank?: number;
}

export interface SimulationResult {
    baseline_score: number;
    simulated_score: number;
    delta: number;
    risk_level: RiskZone;
    top_reasons: RiskReason[];
    shap_values: Record<string, number>;
}
export interface CustomerHistoryItem {
    prediction_id: number;
    snapshot_date: string;
    score: number;
    risk_level: RiskZone;
    top_reasons: RiskReason[];
    model_version: string | null;
    delta: number | null;
}

export interface CustomerHistoryResponse {
    customer_id: number;
    items: CustomerHistoryItem[];
}
