"use client";

import { useAuth } from "@/features/auth/context/auth-context";
import { ImportMappingForm } from "@/features/imports/components/import-mapping-form";

export default function ImportsPage() {
  const { user, loading } = useAuth();

  if (loading) {
    return <main className="p-6 text-black">Chargement…</main>;
  }

  if (!user || user.role === "viewer") {
    return (
      <main className="mx-auto max-w-3xl space-y-3 p-6 text-black">
        <h1 className="text-2xl font-bold text-black">Import de fichiers</h1>
        <p className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-blue-900">
          Votre rôle (lecture seule) ne permet pas d&apos;importer des fichiers.
          Vous pouvez consulter l&apos;historique des imports.
        </p>
      </main>
    );
  }

  return <ImportMappingForm />;
}
