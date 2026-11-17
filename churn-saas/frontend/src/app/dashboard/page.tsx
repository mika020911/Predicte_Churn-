"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type CustomerSummary = {
  total: number;
  zone_counts: {
    low: number;
    medium: number;
    high: number;
  };
};

type ImportSummary = {
  import_batch_id: number;
  filename: string;
  status: string;
  total_rows: number;
  imported_rows: number;
  error_rows: number;
  created_at: string;
};

function formatDate(value: string) {
  return new Date(value).toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function DashboardPage() {
  const { user, token, loading: authLoading } = useAuth();

  const [customers, setCustomers] = useState<CustomerSummary | null>(null);
  const [imports, setImports] = useState<ImportSummary[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;

    if (!token) {
      setLoadingData(false);
      setError("Connecte-toi pour consulter le tableau de bord.");
      return;
    }

    let cancelled = false;

    async function loadDashboard() {
      setLoadingData(true);
      setError(null);

      try {
        const headers = {
          Authorization: `Bearer ${token}`,
        };

        const [customersResponse, importsResponse] = await Promise.all([
          fetch(`${API_URL}/customers?page=1&page_size=1`, {
            headers,
            cache: "no-store",
          }),
          fetch(`${API_URL}/imports/`, {
            headers,
            cache: "no-store",
          }),
        ]);

        if (!customersResponse.ok || !importsResponse.ok) {
          throw new Error("Impossible de charger les données du tableau de bord.");
        }

        const [customerData, importData] = await Promise.all([
          customersResponse.json(),
          importsResponse.json(),
        ]);

        if (!cancelled) {
          setCustomers(customerData);
          setImports(importData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Une erreur est survenue au chargement.",
          );
        }
      } finally {
        if (!cancelled) setLoadingData(false);
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [token, authLoading]);

  const firstName = user?.full_name?.trim().split(/\s+/)[0];

  const stats = [
    {
      label: "Clients évalués",
      value: customers?.total,
      detail: "Avec une prédiction active",
      color: "bg-blue-100",
    },
    {
      label: "Risque élevé",
      value: customers?.zone_counts.high,
      detail: "Clients classés dans la zone élevée",
      color: "bg-red-100",
    },
    {
      label: "Imports réalisés",
      value: imports.length,
      detail: "Fichiers importés par l’organisation",
      color: "bg-violet-100",
    },
  ];

  return (
    <div className="space-y-8">
      <section className="relative isolate overflow-hidden rounded-3xl bg-blue-950 p-6 text-white sm:p-10">
        <div
          aria-hidden="true"
          className="absolute -right-10 -top-20 -z-10 h-72 w-72 rounded-full bg-blue-500/40 blur-3xl"
        />
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-200">
            Tableau de bord
          </p>
          <h2 className="mt-3 text-3xl font-bold sm:text-4xl">
            Bonjour{firstName ? ` ${firstName}` : ""}
          </h2>
          <p className="mt-3 max-w-2xl leading-7 text-white">
            Suis l’activité de ton organisation, importe des données et
            consulte les clients qui nécessitent ton attention.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/dashboard/imports"
              className="rounded-xl bg-white px-5 py-3 font-semibold text-blue-950 hover:bg-blue-50"
            >
              Importer un fichier
            </Link>
            <Link
              href="/dashboard/customers"
              className="rounded-xl border border-white/60 px-5 py-3 font-semibold text-white hover:bg-white/10"
            >
              Voir les clients
            </Link>
          </div>
        </div>
      </section>

      {error && (
        <p
          role="alert"
          className="rounded-xl border border-red-300 bg-red-50 p-4 font-medium text-red-950"
        >
          {error}
        </p>
      )}

      <section aria-label="Indicateurs principaux">
        <div className="mb-4">
          <p className="font-semibold text-blue-900">Vue d’ensemble</p>
          <h2 className="mt-1 text-2xl font-bold text-black">
            Activité de votre organisation
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {stats.map((stat) => (
            <article
              key={stat.label}
              className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-black">{stat.label}</p>
                  <p className="mt-2 text-sm text-black">{stat.detail}</p>
                </div>
                <span
                  aria-hidden="true"
                  className={`h-3 w-3 shrink-0 rounded-full ${stat.color}`}
                />
              </div>

              <p className="mt-6 text-4xl font-bold text-black">
                {loadingData ? "…" : stat.value ?? 0}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold text-blue-900">Imports</p>
              <h2 className="mt-1 text-xl font-bold text-black">
                Activité récente
              </h2>
            </div>
            <Link
              href="/dashboard/imports/history"
              className="font-semibold text-blue-900 underline underline-offset-4"
            >
              Tout l’historique
            </Link>
          </div>

          {loadingData ? (
            <p className="py-8 text-black">Chargement des imports…</p>
          ) : imports.length === 0 ? (
            <div className="mt-5 rounded-xl bg-blue-50 p-5">
              <p className="font-semibold text-black">
                Aucun import pour le moment.
              </p>
              <Link
                href="/dashboard/imports"
                className="mt-3 inline-block font-semibold text-blue-900 underline underline-offset-4"
              >
                Importer votre premier CSV
              </Link>
            </div>
          ) : (
            <div className="mt-5 divide-y divide-blue-100">
              {imports.slice(0, 5).map((item) => (
                <Link
                  key={item.import_batch_id}
                  href={`/dashboard/imports/${item.import_batch_id}`}
                  className="flex flex-col gap-2 py-4 transition hover:bg-blue-50 sm:flex-row sm:items-center sm:justify-between sm:px-3"
                >
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-black">
                      {item.filename}
                    </p>
                    <p className="mt-1 text-sm text-black">
                      {formatDate(item.created_at)}
                    </p>
                  </div>
                  <div className="flex gap-4 text-sm text-black">
                    <span>{item.imported_rows} importées</span>
                    <span>{item.error_rows} erreurs</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm sm:p-6">
          <p className="font-semibold text-blue-900">Accès rapides</p>
          <h2 className="mt-1 text-xl font-bold text-black">
            Continuer votre travail
          </h2>

          <div className="mt-5 space-y-3">
            <Link
              href="/dashboard/customers"
              className="flex items-center justify-between rounded-xl border border-blue-100 p-4 font-semibold text-black transition hover:bg-blue-50"
            >
              Consulter les clients
              <span aria-hidden="true" className="text-blue-900">→</span>
            </Link>

            <Link
              href="/dashboard/imports"
              className="flex items-center justify-between rounded-xl border border-blue-100 p-4 font-semibold text-black transition hover:bg-blue-50"
            >
              Lancer un nouvel import
              <span aria-hidden="true" className="text-blue-900">→</span>
            </Link>

            <Link
              href="/dashboard/imports/history"
              className="flex items-center justify-between rounded-xl border border-blue-100 p-4 font-semibold text-black transition hover:bg-blue-50"
            >
              Ouvrir l’historique
              <span aria-hidden="true" className="text-blue-900">→</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}