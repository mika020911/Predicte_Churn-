"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { canManageSettings } from "@/features/auth/permissions";
import { getRiskSettings, updateRiskSettings } from "../api/risk-settings-api";

function formatDate(value: string | null): string {
  if (!value) return "jamais";
  return new Date(value).toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function toPercent(value: string): number {
  return Math.round(Number(value));
}

export function RiskSettingsForm() {
  const { token, user, loading: authLoading } = useAuth();
  const canEdit = canManageSettings(user?.role);

  const [thresholdMedium, setThresholdMedium] = useState("");
  const [thresholdHigh, setThresholdHigh] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;

    if (!token) {
      setError("Connecte-toi pour consulter les paramètres.");
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadSettings() {
      setLoading(true);
      setError(null);

      try {
        const settings = await getRiskSettings(token as string);
        if (cancelled) return;

        setThresholdMedium(String(Math.round(settings.threshold_medium * 100)));
        setThresholdHigh(String(Math.round(settings.threshold_high * 100)));
        setUpdatedAt(settings.updated_at);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger les seuils de risque.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadSettings();

    return () => {
      cancelled = true;
    };
  }, [token, authLoading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!canEdit) {
      setError("Seul un administrateur peut modifier les seuils de risque.");
      return;
    }

    if (!token) {
      setError("Connecte-toi pour modifier les paramètres.");
      return;
    }

    const medium = toPercent(thresholdMedium);
    const high = toPercent(thresholdHigh);

    if (!Number.isFinite(medium) || !Number.isFinite(high)) {
      setError("Les seuils doivent être des nombres.");
      return;
    }

    if (medium <= 0 || medium >= 100 || high <= 0 || high >= 100) {
      setError("Chaque seuil doit être strictement compris entre 0 % et 100 %.");
      return;
    }

    if (medium >= high) {
      setError("Le seuil moyen doit être strictement inférieur au seuil haut.");
      return;
    }

    setSaving(true);

    try {
      const settings = await updateRiskSettings(token, {
        threshold_medium: medium / 100,
        threshold_high: high / 100,
      });

      setThresholdMedium(String(Math.round(settings.threshold_medium * 100)));
      setThresholdHigh(String(Math.round(settings.threshold_high * 100)));
      setUpdatedAt(settings.updated_at);
      setSuccess(
        "Seuils enregistrés. Les prédictions existantes ont été reclassées.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible d’enregistrer les seuils de risque.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="p-6 text-black">Chargement des paramètres…</main>
    );
  }

  const medium = toPercent(thresholdMedium);
  const high = toPercent(thresholdHigh);
  const mediumValid = Number.isFinite(medium) && medium > 0 && medium < 100;
  const highValid = Number.isFinite(high) && high > 0 && high < 100;

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-6 text-black">
      <header>
        <h1 className="text-3xl font-bold text-black">Paramètres</h1>
        <p className="mt-2 text-black">
          Ajuste les seuils qui définissent les zones de risque de ton
          organisation. Chaque score est comparé à ces seuils.
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-900"
        >
          {error}
        </p>
      )}

      {success && (
        <p
          role="status"
          aria-live="polite"
          className="rounded-xl border border-green-300 bg-green-50 p-4 text-green-900"
        >
          {success}
        </p>
      )}

      {!canEdit && (
        <p className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-blue-900">
          Lecture seule : seul un administrateur peut modifier ces seuils.
        </p>
      )}

      <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">Zones de risque</h2>
        <p className="mt-1 text-sm text-black">
          Aperçu avec les valeurs actuellement saisies.
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <article className="rounded-xl border border-green-200 bg-green-50 p-4">
            <p className="font-semibold text-green-900">Faible</p>
            <p className="mt-1 text-sm text-green-900">
              score &lt; {mediumValid ? `${medium} %` : "seuil moyen"}
            </p>
          </article>
          <article className="rounded-xl border border-orange-200 bg-orange-50 p-4">
            <p className="font-semibold text-orange-900">Moyen</p>
            <p className="mt-1 text-sm text-orange-900">
              {mediumValid ? `${medium} %` : "seuil moyen"} ≤ score &lt;{" "}
              {highValid ? `${high} %` : "seuil haut"}
            </p>
          </article>
          <article className="rounded-xl border border-red-200 bg-red-50 p-4">
            <p className="font-semibold text-red-900">Élevé</p>
            <p className="mt-1 text-sm text-red-900">
              score ≥ {highValid ? `${high} %` : "seuil haut"}
            </p>
          </article>
        </div>
      </section>

      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm"
      >
        <div>
          <h2 className="text-xl font-bold text-black">
            Modifier les seuils
          </h2>
          <p className="mt-1 text-sm text-black">
            Valeurs en pourcentage. Le seuil moyen doit rester inférieur au
            seuil haut.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-black">
              Seuil moyen (%)
            </span>
            <input
              type="number"
              required
              min={1}
              max={99}
              step={1}
              value={thresholdMedium}
              disabled={!canEdit || saving}
              onChange={(event) => {
                setThresholdMedium(event.target.value);
                setSuccess(null);
              }}
              className="w-full rounded-xl border border-blue-200 px-4 py-3 text-black outline-none transition focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
            />
            <span className="mt-1 block text-xs text-black">
              À partir de ce score, le client passe en zone moyenne.
            </span>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-black">
              Seuil haut (%)
            </span>
            <input
              type="number"
              required
              min={1}
              max={99}
              step={1}
              value={thresholdHigh}
              disabled={!canEdit || saving}
              onChange={(event) => {
                setThresholdHigh(event.target.value);
                setSuccess(null);
              }}
              className="w-full rounded-xl border border-blue-200 px-4 py-3 text-black outline-none transition focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
            />
            <span className="mt-1 block text-xs text-black">
              À partir de ce score, le client passe en zone élevée.
            </span>
          </label>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-black">
            Dernière modification : {formatDate(updatedAt)}
          </p>

          {canEdit && (
            <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setThresholdMedium("40");
                setThresholdHigh("70");
                setSuccess(null);
                setError(null);
              }}
              disabled={saving}
              className="rounded-xl border border-blue-200 px-5 py-3 font-semibold text-black transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Valeurs par défaut
            </button>

            <button
              type="submit"
              disabled={saving}
              className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Enregistrement…" : "Enregistrer"}
            </button>
            </div>
          )}
        </div>
      </form>
    </main>
  );
}
