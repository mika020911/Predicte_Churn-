import numpy as np
import pandas as pd

from config import CHURN_RATE, ID_COLUMN, N_SAMPLES, RANDOM_STATE, RAW_DATA_PATH


def find_bias(score, target, lo=-10.0, hi=10.0, iters=50):
    """Décale le score pour que la probabilité moyenne de départ vaille `target`."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        if (1 / (1 + np.exp(-(score + mid)))).mean() < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def generate_churn_dataset(n_samples=N_SAMPLES, churn_rate=CHURN_RATE, seed=RANDOM_STATE):
    """Génère un dataset synthétique avec des corrélations réalistes."""
    rng = np.random.default_rng(seed)

    # Ancienneté : beaucoup de clients récents, peu d'anciens
    tenure_months = np.clip(
        rng.lognormal(mean=2.5, sigma=0.8, size=n_samples).astype(int), 1, 120
    )

    # Contrat : 0 = mensuel, 1 = annuel (plus fréquent chez les anciens)
    prob_annual = np.clip(0.15 + tenure_months / 200, 0, 0.7)
    contract_type = rng.binomial(1, prob_annual)

    # Variation du revenu mensuel (%), plus stable pour les contrats annuels
    base_mrr_change = rng.normal(0, 8, size=n_samples)
    mrr_change_pct = np.round(
        np.where(contract_type == 1, base_mrr_change * 0.4, base_mrr_change), 2
    )

    # Tickets de support : les clients récents en ouvrent plus
    ticket_rate = np.clip(2.5 - tenure_months / 40, 0.3, 4.0)
    support_tickets_30d = rng.poisson(ticket_rate)

    # Jours depuis la dernière activité
    recency_days = np.clip(
        rng.lognormal(mean=1.5, sigma=0.9, size=n_samples).astype(int), 0, 90
    )

    # Tendance de fréquence d'usage (1.0 = stable, < 1 = en baisse)
    frequency_trend_30d = np.round(
        np.clip(rng.normal(1.0, 0.25, size=n_samples) - recency_days / 200, 0.1, 2.0), 3
    )

    # Part des fonctionnalités utilisées (0 à 1)
    engagement_breadth = np.round(
        np.clip(rng.beta(3, 2, size=n_samples) + tenure_months / 300, 0.05, 1.0), 3
    )

    # Échecs de paiement sur 90 jours : plus fréquents chez les mensuels
    payment_failures_90d = rng.poisson(np.where(contract_type == 1, 0.1, 0.4))

    # Date du snapshot, répartie sur 6 mois (pour un split temporel)
    snapshot_date = pd.Timestamp("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 180, size=n_samples), unit="D"
    )

    SIGNAL_STRENGTH = 2.0   # ajoute cette ligne en haut de generate_churn_dataset

    signal = (
        -0.03 * tenure_months
        - 0.8 * contract_type
        + 0.02 * np.clip(-mrr_change_pct, 0, None)
        + 0.15 * support_tickets_30d
        + 0.04 * recency_days
        - 1.5 * (frequency_trend_30d - 1)
        - 1.2 * engagement_breadth
        + 0.6 * payment_failures_90d
    )
    latent_score = SIGNAL_STRENGTH * signal + rng.normal(0, 0.8, size=n_samples)
    latent_score += find_bias(latent_score, churn_rate)
    prob_churn = 1 / (1 + np.exp(-latent_score))
    churn = rng.binomial(1, prob_churn)

    return pd.DataFrame(
        {
            ID_COLUMN: [f"C{i:05d}" for i in range(n_samples)],
            "snapshot_date": snapshot_date,
            "tenure_months": tenure_months,
            "contract_type": contract_type,
            "mrr_change_pct": mrr_change_pct,
            "support_tickets_30d": support_tickets_30d,
            "recency_days": recency_days,
            "frequency_trend_30d": frequency_trend_30d,
            "engagement_breadth": engagement_breadth,
            "payment_failures_90d": payment_failures_90d,
            "churn": churn,
        }
    )


def main():
    print("Génération du jeu de données synthétique...")
    df = generate_churn_dataset()
    print(f"  Lignes        : {len(df)}")
    print(f"  Taux de churn : {df['churn'].mean():.2%}")
    print(f"  Période       : {df['snapshot_date'].min().date()} -> {df['snapshot_date'].max().date()}")
    df.to_csv(RAW_DATA_PATH, index=False)
    print(f"Fichier sauvegardé : {RAW_DATA_PATH}")


if __name__ == "__main__":
    main()