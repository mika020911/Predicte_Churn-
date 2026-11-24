"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { getPlanOptions } from "@/features/imports/api/imports-api";
import type { PlanOption } from "@/features/imports/types";
import { simulateCustomer } from "../api/customers-api";
import { formatScore, zoneBadgeClass, zoneLabel } from "../risk";
import type {
  CustomerObservation,
  SimulationPayload,
  SimulationResult,
} from "../types";

type FieldKey = keyof SimulationPayload;

type NumericField = {
  key: Exclude<FieldKey, "contract_type" | "plan_tier_rank">;
  label: string;
  min?: number;
  max?: number;
  step: number;
};

const NUMERIC_FIELDS: NumericField[] = [
  { key: "tenure_months", label: "Ancienneté (mois)", min: 0, step: 1 },
  { key: "mrr_change_pct", label: "Variation du revenu mensuel (%)", step: 0.1 },
  { key: "support_tickets_30d", label: "Tickets support (30 j)", min: 0, step: 1 },
  { key: "recency_days", label: "Dernière activité (jours)", min: 0, step: 1 },
  { key: "frequency_trend_30d", label: "Tendance d’usage (30 j)", step: 0.01 },
  {
    key: "engagement_breadth",
    label: "Fonctionnalités utilisées (0–1)",
    min: 0,
    max: 1,
    step: 0.01,
  },
  {
    key: "payment_failures_90d",
    label: "Échecs de paiement (90 j)",
    min: 0,
    step: 1,
  },
];

type SimulationValues = {
  [K in FieldKey]: K extends "contract_type" ? 0 | 1 : number;
};

function initialValues(observation: CustomerObservation): SimulationValues {
  return {
    tenure_months: observation.tenure_months,
    contract_type: observation.contract_type === 1 ? 1 : 0,
    mrr_change_pct: observation.mrr_change_pct,
    support_tickets_30d: observation.support_tickets_30d,
    recency_days: observation.recency_days,
    frequency_trend_30d: observation.frequency_trend_30d,
    engagement_breadth: observation.engagement_breadth,
    payment_failures_90d: observation.payment_failures_90d,
    plan_tier_rank: observation.plan_tier_rank,
  };
}

function planLabel(name: string): string {
  if (!name) return name;
  return name.charAt(0).toUpperCase() + name.slice(1);
}

function formatDelta(delta: number): string {
  const points = Math.round(delta * 100);
  if (points === 0) return "0 point";
  return `${points > 0 ? "+" : ""}${points} point${Math.abs(points) > 1 ? "s" : ""}`;
}

export function ScoreSimulator({
  customerId,
  observation,
}: {
  customerId: number;
  observation: CustomerObservation;
}) {
  const { token } = useAuth();
  const baseline = useMemo(() => initialValues(observation), [observation]);

  const [values, setValues] = useState<SimulationValues>(baseline);
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    getPlanOptions(token)
      .then((options) => {
        if (!cancelled) setPlans(options);
      })
      .catch(() => {
        // La liste des plans est optionnelle : le champ reste désactivé.
        if (!cancelled) setPlans([]);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      setSimulating(true);
      try {
        const simulated = await simulateCustomer(token, customerId, values);
        if (!cancelled) {
          setResult(simulated);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "La simulation a échoué.",
          );
        }
      } finally {
        if (!cancelled) setSimulating(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [token, customerId, values]);

  function update<K extends FieldKey>(key: K, value: SimulationValues[K]) {
    if (!Number.isFinite(value)) return;
    setValues((current) => ({ ...current, [key]: value }));
  }

  function reset() {
    setValues(baseline);
    setError(null);
  }

  const planDisabled = plans.length <= 1;
  const selectedPlanIndex = plans.findIndex(
    (plan) => Math.abs(plan.rank - values.plan_tier_rank) < 0.0001,
  );

  return (
    <section className="space-y-4 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-black">Simuler un scénario</h2>
          <p className="mt-1 text-sm text-black">
            Modifie les valeurs : le score est recalculé à la volée. Rien n’est
            enregistré.
          </p>
        </div>
        <button
          type="button"
          onClick={reset}
          className="h-fit rounded-xl border border-blue-200 px-4 py-2 text-sm font-semibold text-blue-900 hover:bg-blue-50"
        >
          Réinitialiser
        </button>
      </div>

      <p className="rounded-xl bg-blue-50 px-4 py-3 text-sm text-blue-950">
        Ce que le modèle prédit, pas une garantie.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {NUMERIC_FIELDS.map((field) => (
          <label key={field.key} className="block">
            <span className="mb-1 block text-sm font-medium text-black">
              {field.label}
            </span>
            <input
              type="number"
              min={field.min}
              max={field.max}
              step={field.step}
              value={values[field.key]}
              onChange={(event) => update(field.key, Number(event.target.value))}
              className="w-full rounded-xl border border-blue-200 px-3 py-2 text-black outline-none focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
            />
          </label>
        ))}

        <label className="block">
          <span className="mb-1 block text-sm font-medium text-black">
            Type de contrat
          </span>
          <select
            value={values.contract_type}
            onChange={(event) =>
              update("contract_type", Number(event.target.value) === 1 ? 1 : 0)
            }
            className="w-full rounded-xl border border-blue-200 px-3 py-2 text-black outline-none focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
          >
            <option value={0}>Mensuel</option>
            <option value={1}>Annuel</option>
          </select>
        </label>

        <label className="block">
          <span className="mb-1 block text-sm font-medium text-black">
            Gamme du plan
          </span>
          <select
            value={selectedPlanIndex >= 0 ? selectedPlanIndex : ""}
            disabled={planDisabled}
            onChange={(event) =>
              update("plan_tier_rank", plans[Number(event.target.value)].rank)
            }
            className="w-full rounded-xl border border-blue-200 px-3 py-2 text-black outline-none disabled:bg-slate-100 focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
          >
            {plans.length === 0 && <option value="">Non renseigné</option>}
            {plans.length === 1 && (
              <option value={0}>{planLabel(plans[0].name)}</option>
            )}
            {plans.map((plan, index) => (
              <option key={plan.name} value={index}>
                {planLabel(plan.name)}
              </option>
            ))}
            {plans.length > 1 && selectedPlanIndex < 0 && (
              <option value="">Valeur actuelle ({values.plan_tier_rank})</option>
            )}
          </select>
          {planDisabled && (
            <span className="mt-1 block text-xs text-black">
              Un seul plan (ou aucun) : la gamme n’est pas modifiable.
            </span>
          )}
        </label>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-950"
        >
          {error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <article className="rounded-xl border border-blue-100 p-4">
          <p className="text-sm text-black">Score actuel</p>
          <p className="mt-1 text-2xl font-bold text-black">
            {formatScore(result?.baseline_score ?? 0)}
          </p>
        </article>
        <article className="rounded-xl border border-blue-100 p-4">
          <p className="text-sm text-black">Score simulé</p>
          <p className="mt-1 text-2xl font-bold text-black">
            {result ? formatScore(result.simulated_score) : "…"}
          </p>
          {simulating && (
            <p className="mt-1 text-xs text-blue-900">Calcul en cours…</p>
          )}
        </article>
        <article className="rounded-xl border border-blue-100 p-4">
          <p className="text-sm text-black">Écart</p>
          <p className="mt-1 text-2xl font-bold text-black">
            {result ? formatDelta(result.delta) : "…"}
          </p>
          {result && (
            <span
              className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${zoneBadgeClass(
                result.risk_level,
              )}`}
            >
              Zone {zoneLabel(result.risk_level).toLowerCase()}
            </span>
          )}
        </article>
      </div>

      {result && result.top_reasons.length > 0 && (
        <div>
          <h3 className="font-semibold text-black">
            Principales raisons du score simulé
          </h3>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-black">
            {result.top_reasons.map((reason, index) => (
              <li key={`${reason.feature}-${index}`}>{reason.message}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
