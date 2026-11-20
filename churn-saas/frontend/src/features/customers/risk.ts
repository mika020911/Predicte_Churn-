import type { RiskZone } from "./types";

/** Affichage partagé du score et des zones de risque (liste + fiche client). */

export function formatScore(score: number): string {
  return `${Math.round(score * 100)} %`;
}

export function zoneLabel(zone: RiskZone): string {
  switch (zone) {
    case "low":
      return "Faible";
    case "medium":
      return "Moyen";
    case "high":
      return "Élevé";
  }
}

export function zoneBadgeClass(zone: RiskZone): string {
  switch (zone) {
    case "low":
      return "bg-green-100 text-green-800";
    case "medium":
      return "bg-orange-100 text-orange-800";
    case "high":
      return "bg-red-100 text-red-800";
  }
}

export const FEATURE_LABELS: Record<string, string> = {
  tenure_months: "Ancienneté",
  contract_type: "Type de contrat",
  mrr_change_pct: "Variation du revenu mensuel",
  support_tickets_30d: "Tickets support (30 j)",
  recency_days: "Dernière activité",
  frequency_trend_30d: "Tendance d’usage (30 j)",
  engagement_breadth: "Fonctionnalités utilisées",
  payment_failures_90d: "Échecs de paiement (90 j)",
  plan_tier_rank: "Gamme du plan",
};

export function featureLabel(feature: string): string {
  return FEATURE_LABELS[feature] ?? feature;
}
