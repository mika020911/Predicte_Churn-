"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@/features/auth/context/auth-context";
import { getImportDetails } from "../api/imports-api";
import type { ImportBatch } from "../types";

export function ImportDetails() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();

  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDetails() {
      const importId = Number(params.id);

      if (!token) {
        setError("Connecte-toi pour consulter ce rapport.");
        setLoading(false);
        return;
      }

      if (!Number.isInteger(importId) || importId < 1) {
        setError("Identifiant d’import invalide.");
        setLoading(false);
        return;
      }

      try {
        const result = await getImportDetails(token, importId);
        if (!cancelled) setBatch(result);
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

    void loadDetails();

    return () => {
      cancelled = true;
    };
  }, [token, params.id]);

  if (loading) {
    return <main className="p-6 text-black">Chargement du rapport…</main>;
  }

  if (error) {
    return (
      <main className="space-y-4 p-6 text-black">
        <p role="alert" className="text-red-900">{error}</p>
        <Link
          href="/dashboard/imports/history"
          className="text-blue-800 underline"
        >
          Retour à l’historique
        </Link>
      </main>
    );
  }

  if (!batch) return null;

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6 text-black">
      <Link
        href="/dashboard/imports/history"
        className="text-blue-800 underline"
      >
        ← Retour à l’historique
      </Link>

      <header>
        <h1 className="text-3xl font-bold text-black">Rapport d’import</h1>
        <p className="mt-2 text-black">
          Fichier : {batch.filename} — statut : {batch.status}
        </p>
      </header>

      {batch.error_message && (
        <p className="rounded-md border border-orange-300 bg-orange-50 p-4 text-orange-950">
          {batch.error_message}
        </p>
      )}

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-300 p-4">
          <p className="text-black">Lignes lues</p>
          <p className="text-2xl font-bold text-black">{batch.total_rows}</p>
        </div>
        <div className="rounded-lg border border-slate-300 p-4">
          <p className="text-black">Importées</p>
          <p className="text-2xl font-bold text-green-800">
            {batch.imported_rows}
          </p>
        </div>
        <div className="rounded-lg border border-slate-300 p-4">
          <p className="text-black">En erreur</p>
          <p className="text-2xl font-bold text-red-800">{batch.error_rows}</p>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xl font-bold text-black">
          Anomalies ({batch.anomaly_report?.length ?? 0})
        </h2>

        {!batch.anomaly_report?.length ? (
          <p className="text-black">Aucune anomalie signalée.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-300">
            <table className="min-w-full text-left">
              <thead className="bg-slate-50">
                <tr className="text-black">
                  <th className="px-4 py-3">Ligne</th>
                  <th className="px-4 py-3">Client</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Détail</th>
                </tr>
              </thead>
              <tbody>
                {batch.anomaly_report.map((anomaly, index) => (
                  <tr
                    key={`${anomaly.row_number}-${index}`}
                    className="border-t border-slate-200 text-black"
                  >
                    <td className="px-4 py-3">{anomaly.row_number}</td>
                    <td className="px-4 py-3">
                      {anomaly.external_id ?? "—"}
                    </td>
                    <td className="px-4 py-3">{anomaly.error_type}</td>
                    <td className="px-4 py-3">{anomaly.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}