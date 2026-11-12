"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { getCustomers } from "../api/customers-api";
import type {
  CustomerListResponse,
  RiskZone,
} from "../types";

type ZoneFilter = RiskZone | "all";

const PAGE_SIZE = 20;

const ZONES: Array<{ value: ZoneFilter; label: string }> = [
  { value: "all", label: "Tous" },
  { value: "low", label: "Faible" },
  { value: "medium", label: "Moyen" },
  { value: "high", label: "Élevé" },
];

function formatScore(score: number): string {
  return `${Math.round(score * 100)} %`;
}

function zoneLabel(zone: RiskZone): string {
  switch (zone) {
    case "low":
      return "Faible";
    case "medium":
      return "Moyen";
    case "high":
      return "Élevé";
  }
}

function zoneBadgeClass(zone: RiskZone): string {
  switch (zone) {
    case "low":
      return "bg-green-100 text-green-800";
    case "medium":
      return "bg-orange-100 text-orange-800";
    case "high":
      return "bg-red-100 text-red-800";
  }
}

export function CustomerList() {
  const { token, loading: authLoading } = useAuth();

  const [data, setData] = useState<CustomerListResponse | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [zone, setZone] = useState<ZoneFilter>("all");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Attend 300 ms après la saisie avant de déclencher la recherche.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPage(1);
      setSearch(searchInput.trim());
    }, 300);

    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const loadCustomers = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getCustomers(token, {
        search,
        zone: zone === "all" ? undefined : zone,
        page,
        page_size: PAGE_SIZE,
      });

      setData(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Une erreur est survenue.",
      );
    } finally {
      setLoading(false);
    }
  }, [token, search, zone, page]);

  useEffect(() => {
    if (!authLoading && token) {
      void loadCustomers();
    } else if (!authLoading && !token) {
      setLoading(false);
      setError("Connecte-toi pour consulter les clients.");
    }
  }, [authLoading, token, loadCustomers]);

  function selectZone(nextZone: ZoneFilter) {
    setZone(nextZone);
    setPage(1);
  }

  const totalPages = data?.total_pages ?? 0;

  return (
    <section className="mx-auto max-w-6xl space-y-6 p-6 text-black">
      <header>
        <h1 className="text-3xl font-bold text-black">
          Clients
        </h1>
        <p className="mt-1 text-black">
          Recherche et suivi du risque de départ.
        </p>
      </header>

      <label className="block">
        <span className="sr-only">Rechercher un client</span>
        <input
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Rechercher par nom ou identifiant…"
          className="w-full rounded-lg border border-slate-300 px-4 py-3 text-black placeholder:text-black outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </label>

      <nav
        aria-label="Filtrer par zone de risque"
        className="flex flex-wrap gap-2"
      >
        {ZONES.map((item) => {
          const count =
            item.value === "all"
              ? data?.zone_counts
                ? Object.values(data.zone_counts).reduce(
                    (sum, value) => sum + value,
                    0,
                  )
                : 0
              : data?.zone_counts[item.value] ?? 0;

          const selected = zone === item.value;

          return (
            <button
              key={item.value}
              type="button"
              onClick={() => selectZone(item.value)}
              aria-pressed={selected}
              className={`rounded-full border px-4 py-2 text-sm font-medium ${
                selected
                  ? "border-blue-700 bg-blue-700 text-white"
                  : "border-slate-300 bg-white text-black hover:bg-slate-50"
              }`}
            >
              {item.label} ({count})
            </button>
          );
        })}
      </nav>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800"
        >
          {error}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-sm text-black">
                <th className="px-5 py-3 font-semibold">Client</th>
                <th className="px-5 py-3 font-semibold">Identifiant</th>
                <th className="px-5 py-3 font-semibold">Score</th>
                <th className="px-5 py-3 font-semibold">Zone</th>
                <th className="px-5 py-3 font-semibold">Observation</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-10 text-center text-black"
                  >
                    Chargement des clients…
                  </td>
                </tr>
              ) : data?.items.length ? (
                data.items.map((customer) => (
                  <tr
                    key={customer.customer_id}
                    className="text-black"
                  >
                    <td className="px-5 py-4">
                      <div className="font-medium text-black">
                        {customer.name || "—"}
                      </div>
                      <div className="text-sm text-black">
                        {customer.email || ""}
                      </div>
                    </td>

                    <td className="px-5 py-4 text-sm font-medium text-black">
                      {customer.external_id}
                    </td>

                    <td className="px-5 py-4 font-semibold text-black">
                      {formatScore(customer.score)}
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${zoneBadgeClass(
                          customer.risk_level,
                        )}`}
                      >
                        {zoneLabel(customer.risk_level)}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-sm text-black">
                      {customer.snapshot_date}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-10 text-center text-black"
                  >
                    Aucun client trouvé.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <footer className="flex items-center justify-between gap-4 border-t border-slate-200 px-5 py-4">
          <p className="text-sm text-black">
            {data ? `${data.total} client(s)` : ""}
          </p>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={loading || page <= 1}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-black disabled:cursor-not-allowed disabled:opacity-50"
            >
              Précédent
            </button>

            <span className="min-w-24 text-center text-sm text-black">
              Page {data?.page ?? page} / {totalPages}
            </span>

            <button
              type="button"
              onClick={() =>
                setPage((current) => Math.min(totalPages, current + 1))
              }
              disabled={loading || page >= totalPages || totalPages === 0}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-black disabled:cursor-not-allowed disabled:opacity-50"
            >
              Suivant
            </button>
          </div>
        </footer>
      </div>
    </section>
  );
}