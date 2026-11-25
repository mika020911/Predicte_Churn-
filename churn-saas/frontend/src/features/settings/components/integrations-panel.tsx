"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { canManageSettings } from "@/features/auth/permissions";
import { getApiKeyInfo, rotateApiKey } from "../api/api-key-api";
import type { ApiKeyStatus } from "../types";

const INGEST_URL = `${
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
}/ingest/observations`;

const SAMPLE_PAYLOAD = {
  observations: [
    {
      customer_id: "CLI-1042",
      snapshot_date: "2026-11-01",
      name: "Camille Martin",
      email: "camille.martin@example.com",
      phone_number: "+33612345678",
      tenure_months: 18,
      contract_type: 1,
      mrr_change_pct: -12.5,
      support_tickets_30d: 4,
      recency_days: 9,
      frequency_trend_30d: -0.18,
      engagement_breadth: 0.42,
      payment_failures_90d: 1,
      plan: "Business",
      plan_tier_rank: 0.6,
    },
  ],
};

const CURL_EXAMPLE = `curl -X POST "${INGEST_URL}" \\
  -H "X-API-Key: cs_cle_factice_000000000000000000" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(SAMPLE_PAYLOAD, null, 2)}'`;

function formatDate(value: string | null): string {
  if (!value) return "date inconnue";
  return new Date(value).toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function IntegrationsPanel() {
  const { token, user, loading: authLoading } = useAuth();
  const allowed = canManageSettings(user?.role);

  const [status, setStatus] = useState<ApiKeyStatus | null>(null);
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<"key" | "example" | null>(null);
  const [copyError, setCopyError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || !allowed) return;

    if (!token) {
      setError("Connecte-toi pour gérer les intégrations.");
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadStatus() {
      setLoading(true);
      setError(null);

      try {
        const result = await getApiKeyInfo(token as string);
        if (!cancelled) setStatus(result);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger l’état de la clé API.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadStatus();

    return () => {
      cancelled = true;
    };
  }, [token, authLoading, allowed]);

  // La section n'existe pas pour les rôles sans droit d'administration.
  if (authLoading || !allowed) return null;

  async function handleRotate() {
    if (!token) {
      setError("Connecte-toi pour générer une clé API.");
      return;
    }

    setRotating(true);
    setError(null);
    setCopyError(null);

    try {
      const result = await rotateApiKey(token);
      setStatus({
        exists: result.exists,
        prefix: result.prefix,
        created_at: result.created_at,
      });
      // Seul endroit où la clé en clair vit : l'état React de cette page.
      setRawKey(result.api_key);
      setCopied(null);
      setConfirming(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible de générer la clé API.",
      );
    } finally {
      setRotating(false);
    }
  }

  async function copyText(value: string, target: "key" | "example") {
    setCopyError(null);
    try {
      await navigator.clipboard.writeText(value);
      setCopied(target);
    } catch {
      setCopyError("Copie impossible : sélectionne le texte manuellement.");
    }
  }

  return (
    <section className="mx-auto max-w-4xl space-y-4 px-6 pb-6 text-black">
      <div className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">Intégrations</h2>
        <p className="mt-1 text-sm text-black">
          Envoie des observations directement depuis tes outils via l’API
          d’ingestion, authentifiée par une clé propre à ton organisation.
        </p>

        {error && (
          <p
            role="alert"
            className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-900"
          >
            {error}
          </p>
        )}

        <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-4">
          {loading ? (
            <p className="text-black">Chargement de la clé API…</p>
          ) : status?.exists ? (
            <p className="text-black">
              Clé{" "}
              <code className="rounded bg-white px-1.5 py-0.5 font-mono text-sm">
                {status.prefix ? `${status.prefix}…` : "active"}
              </code>{" "}
              créée le {formatDate(status.created_at)}.
            </p>
          ) : (
            <p className="text-black">
              Aucune clé API n’est configurée pour cette organisation.
            </p>
          )}

          <div className="mt-3 flex flex-wrap gap-3">
            {!status?.exists ? (
              <button
                type="button"
                onClick={() => void handleRotate()}
                disabled={loading || rotating || !token}
                className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {rotating ? "Génération…" : "Générer une clé"}
              </button>
            ) : (
              !confirming && (
                <button
                  type="button"
                  onClick={() => {
                    setConfirming(true);
                    setCopyError(null);
                  }}
                  disabled={rotating || !token}
                  className="rounded-xl border border-orange-300 px-5 py-3 font-semibold text-orange-950 transition hover:bg-orange-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Régénérer
                </button>
              )
            )}
          </div>

          {confirming && (
            <div className="mt-3 rounded-xl border border-orange-300 bg-orange-50 p-4">
              <p className="font-semibold text-orange-950">
                Confirmer la régénération ? L’ancienne clé cessera de
                fonctionner immédiatement.
              </p>
              <div className="mt-3 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void handleRotate()}
                  disabled={rotating}
                  className="rounded-xl bg-orange-700 px-5 py-3 font-semibold text-white transition hover:bg-orange-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {rotating ? "Génération…" : "Confirmer la régénération"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  disabled={rotating}
                  className="rounded-xl border border-orange-300 bg-white px-5 py-3 font-semibold text-orange-950 transition hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Annuler
                </button>
              </div>
            </div>
          )}
        </div>

        {rawKey && (
          <div className="mt-4 rounded-xl border-2 border-blue-700 bg-blue-50 p-4">
            <p className="font-semibold text-blue-950">
              Ta nouvelle clé API (affichée une seule fois)
            </p>
            <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
              <code className="flex-1 break-all rounded-lg border border-blue-200 bg-white px-3 py-2 font-mono text-sm text-black">
                {rawKey}
              </code>
              <button
                type="button"
                onClick={() => void copyText(rawKey, "key")}
                className="rounded-xl border border-blue-300 bg-white px-4 py-2 font-semibold text-blue-950 transition hover:bg-blue-100"
              >
                {copied === "key" ? "Copié !" : "Copier"}
              </button>
            </div>
            <p className="mt-2 text-sm font-semibold text-red-900">
              Elle ne sera plus visible après avoir quitté ou rechargé cette
              page. Conserve-la maintenant.
            </p>
            <button
              type="button"
              onClick={() => {
                setRawKey(null);
                setCopied(null);
              }}
              className="mt-3 rounded-xl border border-blue-300 bg-white px-4 py-2 text-sm font-semibold text-blue-950 transition hover:bg-blue-100"
            >
              J’ai noté la clé
            </button>
          </div>
        )}

        {copyError && (
          <p role="alert" className="mt-3 text-sm text-red-900">
            {copyError}
          </p>
        )}

        <div className="mt-6 border-t border-blue-100 pt-4">
          <h3 className="text-lg font-bold text-black">Exemple d’appel</h3>
          <p className="mt-1 text-sm text-black">
            En-tête <code className="font-mono">X-API-Key</code>, jusqu’à
            5 000 observations par appel, au format interne (noms de colonnes
            internes).
          </p>

          <pre className="mt-3 overflow-x-auto rounded-xl border border-blue-200 bg-slate-950 p-4 text-xs leading-5 text-slate-100">
            <code>{CURL_EXAMPLE}</code>
          </pre>

          <p className="mt-3 text-sm text-black">
            Le format est validé avant l’import : une valeur invalide refuse
            toute la requête (422, avec la position de la ligne). Les doublons
            et les plans inconnus sont signalés ligne par ligne.
          </p>

          <button
            type="button"
            onClick={() => void copyText(CURL_EXAMPLE, "example")}
            className="mt-3 rounded-xl border border-blue-200 px-4 py-2 text-sm font-semibold text-blue-950 transition hover:bg-blue-50"
          >
            {copied === "example" ? "Exemple copié !" : "Copier l’exemple"}
          </button>
        </div>
      </div>
    </section>
  );
}
