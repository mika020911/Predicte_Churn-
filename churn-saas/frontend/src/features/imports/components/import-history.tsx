"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";
import { getImportHistory } from "../api/imports-api";
import type { ImportBatchSummary } from "../types";

function formatDate(value: string): string {
  return new Date(value).toLocaleString("fr-FR");
}

export function ImportHistory() {
  const { token } = useAuth();

  const [imports, setImports] = useState<ImportBatchSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      if (!token) {
        setError("Connecte-toi pour consulter l’historique.");
        setLoading(false);
        return;
      }

      try {
        const result = await getImportHistory(token);
        if (!cancelled) setImports(result);
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

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6 text-black">
      <header>
        <h1 className="text-3xl font-bold text-black">
          Historique des imports
        </h1>
        <p className="mt-2 text-black">
          Consulte les fichiers importés et leurs rapports.
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-red-300 bg-red-50 p-4 text-red-900"
        >
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-300 bg-white">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr className="text-left text-black">
              <th className="px-4 py-3">Fichier</th>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Statut</th>
              <th className="px-4 py-3">Lignes</th>
              <th className="px-4 py-3">Importées</th>
              <th className="px-4 py-3">Erreurs</th>
              <th className="px-4 py-3">Rapport</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-black">
                  Chargement de l’historique…
                </td>
              </tr>
            ) : imports.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-black">
                  Aucun import pour le moment.
                </td>
              </tr>
            ) : (
              imports.map((item) => (
                <tr key={item.import_batch_id} className="text-black">
                  <td className="px-4 py-3 font-medium">{item.filename}</td>
                  <td className="px-4 py-3">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-3">{item.status}</td>
                  <td className="px-4 py-3">{item.total_rows}</td>
                  <td className="px-4 py-3">{item.imported_rows}</td>
                  <td className="px-4 py-3">{item.error_rows}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/imports/${item.import_batch_id}`}
                      className="font-semibold text-blue-800 underline hover:text-blue-950"
                    >
                      Voir le rapport
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}