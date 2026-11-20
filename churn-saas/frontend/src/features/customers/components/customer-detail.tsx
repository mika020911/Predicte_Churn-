"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@/features/auth/context/auth-context";
import { getCustomer } from "../api/customers-api";
import {
  featureLabel,
  formatScore,
  zoneBadgeClass,
  zoneLabel,
} from "../risk";
import type { CustomerDetail as CustomerDetailData } from "../types";

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("fr-FR", {
    dateStyle: "long",
  });
}

function formatMetric(key: string, value: number): string {
  switch (key) {
    case "tenure_months":
      return `${value} mois`;
    case "contract_type":
      return value === 1 ? "Annuel" : "Mensuel";
    case "mrr_change_pct":
      return `${value > 0 ? "+" : ""}${value.toFixed(1)} %`;
    case "recency_days":
      return `il y a ${value} jour${value > 1 ? "s" : ""}`;
    case "frequency_trend_30d":
    case "engagement_breadth":
      return `${Math.round(value * 100)} %`;
    case "plan_tier_rank":
      if (value < 0.34) return "Entrée de gamme";
      if (value < 0.67) return "Gamme intermédiaire";
      return "Haut de gamme";
    default:
      return String(value);
  }
}

type MetricKey =
  | "tenure_months"
  | "contract_type"
  | "mrr_change_pct"
  | "support_tickets_30d"
  | "recency_days"
  | "frequency_trend_30d"
  | "engagement_breadth"
  | "payment_failures_90d"
  | "plan_tier_rank";

const OBSERVATION_KEYS: MetricKey[] = [
  "tenure_months",
  "contract_type",
  "mrr_change_pct",
  "support_tickets_30d",
  "recency_days",
  "frequency_trend_30d",
  "engagement_breadth",
  "payment_failures_90d",
  "plan_tier_rank",
];

export function CustomerDetail() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();

  const [customer, setCustomer] = useState<CustomerDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCustomer() {
      const customerId = Number(params.id);

      if (!token) {
        setError("Connecte-toi pour consulter cette fiche client.");
        setLoading(false);
        return;
      }

      if (!Number.isInteger(customerId) || customerId < 1) {
        setError("Identifiant de client invalide.");
        setLoading(false);
        return;
      }

      try {
        const result = await getCustomer(token, customerId);
        if (!cancelled) setCustomer(result);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Une erreur est survenue.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadCustomer();

    return () => {
      cancelled = true;
    };
  }, [token, params.id]);

  if (loading) {
    return (
      <main className="p-6 text-black">Chargement de la fiche client…</main>
    );
  }

  if (error) {
    return (
      <main className="space-y-4 p-6 text-black">
        <p role="alert" className="text-red-900">
          {error}
        </p>
        <Link
          href="/dashboard/customers"
          className="text-blue-800 underline"
        >
          Retour à la liste des clients
        </Link>
      </main>
    );
  }

  if (!customer) return null;

  const shapEntries = Object.entries(customer.shap_values).sort(
    (a, b) => Math.abs(b[1]) - Math.abs(a[1]),
  );
  const maxImpact = Math.max(
    ...shapEntries.map(([, impact]) => Math.abs(impact)),
    0.0001,
  );

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6 text-black">
      <Link
        href="/dashboard/customers"
        className="inline-block text-blue-800 underline underline-offset-4 hover:text-blue-950"
      >
        ← Retour à la liste des clients
      </Link>

      <header className="flex flex-col gap-4 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-blue-900">
            Fiche client
          </p>
          <h1 className="mt-2 text-3xl font-bold text-black">
            {customer.name || customer.external_id}
          </h1>
          <p className="mt-1 text-black">
            Identifiant : {customer.external_id}
          </p>
          <div className="mt-3 space-y-1 text-sm text-black">
            <p>Email : {customer.email || "—"}</p>
            <p>Téléphone : {customer.phone_number || "—"}</p>
          </div>
        </div>

        <span
          className={`inline-flex h-fit rounded-full px-4 py-2 text-sm font-bold ${zoneBadgeClass(
            customer.risk_level,
          )}`}
        >
          Risque {zoneLabel(customer.risk_level).toLowerCase()}
        </span>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        <article className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">
          <p className="font-semibold text-black">Score de risque</p>
          <p className="mt-2 text-3xl font-bold text-black">
            {formatScore(customer.score)}
          </p>
        </article>
        <article className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">
          <p className="font-semibold text-black">Zone</p>
          <p className="mt-2 text-3xl font-bold text-black">
            {zoneLabel(customer.risk_level)}
          </p>
        </article>
        <article className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">
          <p className="font-semibold text-black">Observation</p>
          <p className="mt-2 text-lg font-bold text-black">
            {formatDate(customer.snapshot_date)}
          </p>
          <p className="mt-1 text-sm text-black">
            Modèle : {customer.model_version || "—"}
          </p>
        </article>
      </section>

      <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">
          Principales raisons du risque
        </h2>
        {customer.top_reasons.length > 0 ? (
          <ul className="mt-4 space-y-3">
            {customer.top_reasons.map((reason, index) => (
              <li
                key={`${reason.feature}-${index}`}
                className="rounded-xl bg-blue-50 px-4 py-3"
              >
                <p className="font-medium text-black">{reason.message}</p>
                <p className="mt-1 text-xs text-black">
                  {featureLabel(reason.feature)} · contribution{" "}
                  {reason.impact > 0 ? "+" : ""}
                  {reason.impact.toFixed(2)}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-black">
            Aucune raison détaillée disponible pour ce client.
          </p>
        )}
      </section>

      <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">
          Données de l’observation
        </h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {OBSERVATION_KEYS.map((key) => (
            <div
              key={key}
              className="rounded-xl border border-blue-100 px-4 py-3"
            >
              <dt className="text-sm text-black">{featureLabel(key)}</dt>
              <dd className="mt-1 text-lg font-semibold text-black">
                {formatMetric(key, customer.observation[key])}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">
          Contribution de chaque variable
        </h2>
        <p className="mt-1 text-sm text-black">
          Une contribution positive augmente le risque, une contribution
          négative le diminue.
        </p>

        {shapEntries.length > 0 ? (
          <ul className="mt-4 space-y-3">
            {shapEntries.map(([feature, impact]) => {
              const width = Math.round(
                (Math.abs(impact) / maxImpact) * 100,
              );
              const positive = impact >= 0;

              return (
                <li key={feature}>
                  <div className="flex items-center justify-between gap-3 text-sm text-black">
                    <span className="font-medium">
                      {featureLabel(feature)}
                    </span>
                    <span className="font-semibold">
                      {impact > 0 ? "+" : ""}
                      {impact.toFixed(3)}
                    </span>
                  </div>
                  <div
                    className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100"
                    role="img"
                    aria-label={`${featureLabel(feature)} : contribution ${impact.toFixed(3)}`}
                  >
                    <div
                      className={`h-full rounded-full ${
                        positive ? "bg-red-500" : "bg-green-600"
                      }`}
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="mt-3 text-black">
            Aucune valeur SHAP enregistrée pour cette prédiction.
          </p>
        )}
      </section>
    </main>
  );
}
