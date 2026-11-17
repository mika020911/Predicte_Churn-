"use client";

import { useState, type ChangeEvent } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import {
  previewCsv,
  saveColumnMapping,
  uploadCsv,
} from "../api/imports-api";
import type {
ImportPreview,
ImportBatch,
} from "../types"

export function ImportMappingForm() {
  const { token } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string | null>>({});
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingImport, setLoadingImport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;

    setFile(selectedFile);
    setPreview(null);
    setMapping({});
    setBatch(null);
    setError(null);
  }

  async function handlePreview() {
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

    setLoadingPreview(true);

    try {
      const result = await previewCsv(token, file);
      setPreview(result);

      const initialMapping: Record<string, string | null> = {};
      for (const field of result.fields) {
        initialMapping[field.field] = field.mapped_to;
      }
      setMapping(initialMapping);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible de lire l’aperçu du CSV.",
      );
    } finally {
      setLoadingPreview(false);
    }
  }

  function updateMapping(field: string, csvColumn: string) {
    setMapping((current) => ({
      ...current,
      [field]: csvColumn || null,
    }));
    setBatch(null);
  }

  function mappingProblems(): string[] {
    if (!preview) return [];

    const problems: string[] = [];

    for (const field of preview.fields) {
      if (field.required && !mapping[field.field]) {
        problems.push(`Le champ obligatoire « ${field.field} » n’est pas associé.`);
      }
    }

    const assignedColumns = Object.values(mapping).filter(
      (value): value is string => Boolean(value),
    );
    const duplicates = [...new Set(
      assignedColumns.filter(
        (column, index) => assignedColumns.indexOf(column) !== index,
      ),
    )];

    if (duplicates.length > 0) {
      problems.push(
        `Une colonne est utilisée plusieurs fois : ${duplicates.join(", ")}.`,
      );
    }

    return problems;
  }

  async function handleImport() {
    setError(null);
    setBatch(null);

    if (!token || !file || !preview) {
      setError("Sélectionne un fichier et prévisualise-le avant l’import.");
      return;
    }

    const problems = mappingProblems();
    if (problems.length > 0) {
      setError(problems.join(" "));
      return;
    }

    setLoadingImport(true);

    try {
      await saveColumnMapping(token, mapping);
      const result = await uploadCsv(token, file, mapping);
      setBatch(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "L’import du fichier a échoué.",
      );
    } finally {
      setLoadingImport(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6 text-black">
      <header>
        <h1 className="text-3xl font-bold text-black">Importer un CSV</h1>
        <p className="mt-2 text-black">
          Choisis un fichier, vérifie ses colonnes et associe-les aux champs
          attendus avant l’import.
        </p>
      </header>

      <section className="space-y-4 rounded-xl border border-slate-300 bg-white p-6">
        <label className="block">
          <span className="mb-2 block font-medium text-black">
            Fichier CSV
          </span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={selectFile}
            className="block w-full text-black"
          />
        </label>

        {file && (
          <p className="text-black">Fichier sélectionné : {file.name}</p>
        )}

        <button
          type="button"
          onClick={handlePreview}
          disabled={!file || loadingPreview || loadingImport}
          className="rounded-md bg-blue-700 px-5 py-2 font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loadingPreview ? "Lecture du fichier…" : "Prévisualiser"}
        </button>

        {error && (
          <p
            role="alert"
            className="rounded-md border border-red-300 bg-red-50 p-3 text-red-900"
          >
            {error}
          </p>
        )}
      </section>

      {preview && (
        <section className="space-y-5 rounded-xl border border-slate-300 bg-white p-6">
          <div>
            <h2 className="text-xl font-bold text-black">
              Association des colonnes
            </h2>
            <p className="mt-1 text-black">
              Les champs marqués « obligatoire » doivent être associés.
            </p>
          </div>

          {preview.fields.map((field) => (
            <label
              key={field.field}
              className="grid gap-2 sm:grid-cols-2 sm:items-center"
            >
              <span className="font-medium text-black">
                {field.field}
                {field.required ? " (obligatoire)" : " (facultatif)"}
              </span>

              <select
                value={mapping[field.field] ?? ""}
                onChange={(event) =>
                  updateMapping(field.field, event.target.value)
                }
                className="rounded-md border border-slate-400 bg-white px-3 py-2 text-black"
              >
                <option value="">— Ne pas associer —</option>
                {preview.csv_columns.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </select>
            </label>
          ))}

          {preview.ignored_columns.length > 0 && (
            <p className="text-black">
              Colonnes non utilisées détectées :{" "}
              {preview.ignored_columns.join(", ")}
            </p>
          )}

          {preview.unknown_contract_values.length > 0 && (
            <p className="rounded-md border border-orange-300 bg-orange-50 p-3 text-orange-950">
              Valeurs de contrat non reconnues :{" "}
              {preview.unknown_contract_values.join(", ")}. Elles pourront
              apparaître comme anomalies à l’import.
            </p>
          )}

          {preview.sample_rows.length > 0 && (
            <div>
              <h3 className="mb-2 font-semibold text-black">
                Aperçu des premières lignes
              </h3>
              <pre className="max-h-64 overflow-auto rounded-md border border-slate-300 bg-white p-3 text-sm text-black">
                {JSON.stringify(preview.sample_rows, null, 2)}
              </pre>
            </div>
          )}

          <button
            type="button"
            onClick={handleImport}
            disabled={loadingImport || loadingPreview}
            className="rounded-md bg-green-700 px-5 py-2 font-semibold text-white hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loadingImport ? "Import en cours…" : "Confirmer et importer"}
          </button>
        </section>
      )}

      {batch && (
        <section
          aria-live="polite"
          className="space-y-3 rounded-xl border border-slate-300 bg-white p-6"
        >
          <h2 className="text-xl font-bold text-black">Rapport d’import</h2>
          <p className="text-black">
            Statut : {batch.status} — lignes lues : {batch.total_rows} —{" "}
            importées : {batch.imported_rows} — erreurs : {batch.error_rows}
          </p>

          {batch.error_message && (
            <p className="text-red-900">{batch.error_message}</p>
          )}

          {batch.anomaly_report && batch.anomaly_report.length > 0 && (
            <ul className="list-inside list-disc space-y-1 text-black">
              {batch.anomaly_report.map((anomaly, index) => (
                <li key={`${anomaly.row_number}-${index}`}>
                  Ligne {anomaly.row_number}
                  {anomaly.external_id
                    ? ` (${anomaly.external_id})`
                    : ""}
                  : {anomaly.message}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}