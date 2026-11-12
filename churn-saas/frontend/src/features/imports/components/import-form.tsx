"use client";

import { useState, type FormEvent } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { uploadCsv } from "../api/imports-api";
import type { ImportBatch } from "../types";

export function ImportForm() {
  const { token } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setBatch(null);

    if (!token) {
      setError("Connecte-toi pour importer un fichier.");
      return;
    }

    if (!file) {
      setError("Sélectionne un fichier CSV.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Le fichier doit avoir l’extension .csv.");
      return;
    }

    setLoading(true);

    try {
      const result = await uploadCsv(token, file);
      setBatch(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Une erreur est survenue pendant l’import.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-6 text-black">
      <header>
        <h1 className="text-3xl font-bold text-black">Importer un CSV</h1>
        <p className="mt-2 text-black">
          Sélectionne ton fichier pour importer les observations clients.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-xl border border-slate-300 bg-white p-6"
      >
        <label className="block">
          <span className="mb-2 block font-medium text-black">
            Fichier CSV
          </span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setBatch(null);
              setError(null);
            }}
            className="block w-full text-black file:mr-4 file:rounded-md file:border-0 file:bg-blue-700 file:px-4 file:py-2 file:font-medium file:text-white hover:file:bg-blue-800"
          />
        </label>

        {file && (
          <p className="text-sm text-black">
            Fichier sélectionné : {file.name}
          </p>
        )}

        {error && (
          <p
            role="alert"
            className="rounded-md border border-red-300 bg-red-50 p-3 text-red-900"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !file}
          className="rounded-md bg-blue-700 px-5 py-2 font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Import en cours…" : "Importer le fichier"}
        </button>
      </form>

      {batch && (
        <section
          aria-live="polite"
          className="space-y-4 rounded-xl border border-slate-300 bg-white p-6"
        >
          <div>
            <h2 className="text-xl font-bold text-black">
              Rapport d’import
            </h2>
            <p className="mt-1 text-black">
              Fichier : {batch.filename} — état : {batch.status}
            </p>
          </div>

          {batch.error_message && (
            <p className="rounded-md border border-orange-300 bg-orange-50 p-3 text-orange-950">
              {batch.error_message}
            </p>
          )}

          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-300 p-4">
              <dt className="text-sm font-medium text-black">Lignes lues</dt>
              <dd className="mt-1 text-2xl font-bold text-black">
                {batch.total_rows}
              </dd>
            </div>
            <div className="rounded-lg border border-slate-300 p-4">
              <dt className="text-sm font-medium text-black">Importées</dt>
              <dd className="mt-1 text-2xl font-bold text-green-800">
                {batch.imported_rows}
              </dd>
            </div>
            <div className="rounded-lg border border-slate-300 p-4">
              <dt className="text-sm font-medium text-black">En erreur</dt>
              <dd className="mt-1 text-2xl font-bold text-red-800">
                {batch.error_rows}
              </dd>
            </div>
          </dl>

          {batch.anomaly_report && batch.anomaly_report.length > 0 ? (
            <div>
              <h3 className="mb-3 font-semibold text-black">
                Anomalies ({batch.anomaly_report.length})
              </h3>

              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse text-left">
                  <thead>
                    <tr className="border-b border-slate-300">
                      <th className="px-3 py-2 text-black">Ligne</th>
                      <th className="px-3 py-2 text-black">Client</th>
                      <th className="px-3 py-2 text-black">Type</th>
                      <th className="px-3 py-2 text-black">Détail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batch.anomaly_report.map((anomaly, index) => (
                      <tr
                        key={`${anomaly.row_number}-${index}`}
                        className="border-b border-slate-200"
                      >
                        <td className="px-3 py-2 text-black">
                          {anomaly.row_number}
                        </td>
                        <td className="px-3 py-2 text-black">
                          {anomaly.external_id ?? "—"}
                        </td>
                        <td className="px-3 py-2 text-black">
                          {anomaly.error_type}
                        </td>
                        <td className="px-3 py-2 text-black">
                          {anomaly.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-black">Aucune anomalie signalée.</p>
          )}
        </section>
      )}
    </main>
  );
}