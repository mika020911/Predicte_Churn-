"""Playbook de rétention : transforme les raisons d'une prédiction en actions.

Chaque suggestion tient compte de la *valeur* de l'observation, pas seulement
du nom de la feature : un MRR en hausse ne déclenche pas « revoir le forfait »,
un contrat déjà annuel ne déclenche pas « proposer l'annuel », etc.
"""

from typing import Any, Iterable, Optional

# Seuils du playbook (volontairement simples et explicites).
RECENCY_DAYS_THRESHOLD = 14
ENGAGEMENT_BREADTH_THRESHOLD = 0.5
PLAN_TIER_RANK_THRESHOLD = 0.5  # 0.5 = gamme inconnue, donc non actionnable

DEFAULT_ACTION = {
    "action_type": "call",
    "label": "Prendre contact avec le client pour évaluer la situation",
    "feature": None,
    "impact": 0.0,
}


def _action(
    action_type: str, label: str, feature: str
) -> dict[str, Any]:
    return {
        "action_type": action_type,
        "label": label,
        "feature": feature,
        "impact": 0.0,
    }


def _suggestion_for_feature(
    feature: Optional[str], observation: Any
) -> Optional[dict[str, Any]]:
    """Suggestion actionnable pour une feature, ou None si la valeur l'exclut."""
    if observation is None or not feature:
        return None

    if feature == "recency_days":
        days = getattr(observation, "recency_days", 0) or 0
        if days >= RECENCY_DAYS_THRESHOLD:
            return _action(
                "call",
                f"Relancer le client pour réactivation (inactif depuis {days} jours)",
                feature,
            )
        return None

    if feature == "payment_failures_90d":
        failures = getattr(observation, "payment_failures_90d", 0) or 0
        if failures > 0:
            return _action(
                "other",
                f"Vérifier le moyen de paiement ({failures} échec(s) sur 90 jours)",
                feature,
            )
        return None

    if feature == "frequency_trend_30d":
        trend = getattr(observation, "frequency_trend_30d", 1.0)
        if trend is not None and trend < 1:
            return _action(
                "onboarding",
                "Planifier une session d'onboarding (fréquence d'usage en baisse)",
                feature,
            )
        return None

    if feature == "engagement_breadth":
        breadth = getattr(observation, "engagement_breadth", 1.0)
        if breadth is not None and breadth < ENGAGEMENT_BREADTH_THRESHOLD:
            return _action(
                "onboarding",
                "Planifier une session d'onboarding (usage limité aux fonctions de base)",
                feature,
            )
        return None

    if feature == "support_tickets_30d":
        tickets = getattr(observation, "support_tickets_30d", 0) or 0
        if tickets > 0:
            return _action(
                "other",
                f"Escalader au support ({tickets} ticket(s) sur 30 jours)",
                feature,
            )
        return None

    if feature == "mrr_change_pct":
        change = getattr(observation, "mrr_change_pct", 0.0) or 0.0
        if change < 0:
            return _action(
                "discount",
                f"Revoir le forfait (MRR en baisse de {abs(change):.1f} %)",
                feature,
            )
        return None

    if feature == "contract_type":
        contract_type = getattr(observation, "contract_type", None)
        if contract_type == 0:
            return _action(
                "email", "Proposer un contrat annuel", feature
            )
        return None

    if feature == "plan_tier_rank":
        rank = getattr(observation, "plan_tier_rank", 1.0)
        if rank is not None and rank < PLAN_TIER_RANK_THRESHOLD:
            return _action(
                "email", "Proposer une montée en gamme", feature
            )
        return None

    # tenure_months n'est pas actionnable, comme toute feature inconnue.
    return None


def suggest_actions(
    observation: Any, top_reasons: Optional[Iterable[dict]]
) -> list[dict[str, Any]]:
    """Trois suggestions maximum, ordonnées par impact décroissant.

    Les raisons viennent de la prédiction active. Si aucune valeur n'est
    actionnable, une action de contact par défaut est proposée.
    """
    reasons = [
        reason
        for reason in (top_reasons or [])
        if isinstance(reason, dict) and reason.get("feature")
    ]
    reasons.sort(
        key=lambda reason: abs(float(reason.get("impact") or 0)),
        reverse=True,
    )

    suggestions: list[dict[str, Any]] = []
    seen_features: set[str] = set()
    for reason in reasons:
        feature = str(reason["feature"])
        if feature in seen_features:
            continue
        suggestion = _suggestion_for_feature(feature, observation)
        if suggestion is None:
            continue
        suggestion["impact"] = round(float(reason.get("impact") or 0), 4)
        suggestions.append(suggestion)
        seen_features.add(feature)
        if len(suggestions) == 3:
            break

    if not suggestions:
        return [dict(DEFAULT_ACTION)]
    return suggestions
