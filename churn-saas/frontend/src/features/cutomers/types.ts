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