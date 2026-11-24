"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";
import { canWrite } from "@/features/auth/permissions";
import { getRetentionUsers, listActions } from "../api/retention-api";
import {
  ACTION_STATUS_CLASSES,
  ACTION_STATUS_LABELS,
  ACTION_STATUS_OPTIONS,
  ACTION_TYPE_LABELS,
  formatActionDate,
  formatActionDateTime,
  isActionOverdue,
} from "../labels";
import type {
  ActionStatus,
  CustomerAction,
  RetentionUser,
} from "../types";

type StatusFilter = ActionStatus | "all";

export function ActionsList() {
  const { token, user, loading: authLoading } = useAuth();
  const writable = canWrite(user?.role);

  const [status, setStatus] = useState<StatusFilter>("all");
  const [owner, setOwner] = useState("");
  const [overdue, setOverdue] = useState(false);
  const [actions, setActions] = useState<CustomerAction[]>([]);
  const [users, setUsers] = useState<RetentionUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !writable) return;
    getRetentionUsers(token)
      .then(setUsers)
      .catch(() => {
        // Le filtre par propriétaire reste masqué si les membres sont
        // illisibles, sans bloquer le journal.
      });
  }, [token, writable]);

  const loadActions = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listActions(token, {
        status: status === "all" ? undefined : status,
        owner: owner ? Number(owner) : undefined,
        overdue,
      });
      setActions(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger les actions.",
      );
    } finally {
      setLoading(false);
    }
  }, [token, status, owner, overdue]);

  useEffect(() => {
    if (authLoading) return;
    if (!token) {
      setLoading(false);
      setError("Connecte-toi pour consulter les actions.");
      return;
    }
    void loadActions();
  }, [authLoading, token, loadActions]);

  return (
    <section className="mx-auto max-w-6xl space-y-6 p-6 text-black">
      <header>
        <h1 className="text-3xl font-bold text-black">Actions de rétention</h1>
        <p className="mt-1 text-black">
          Journal des actions menées sur les clients à risque, toutes fiches
          confondues.
        </p>
      </header>

      <div className="flex flex-col gap-4 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm sm:flex-row sm:items-end">
        <label className="block sm:w-56">
          <span className="mb-1 block text-sm font-semibold text-black">
            Statut
          </span>
          <select
            value={status}
            onChange={(event) =>
              setStatus(event.target.value as StatusFilter)
            }
            className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
          >
            <option value="all">Tous les statuts</option>
            {ACTION_STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {ACTION_STATUS_LABELS[option]}
              </option>
            ))}
          </select>
        </label>

        {users.length > 0 ? (
          <label className="block sm:w-56">
            <span className="mb-1 block text-sm font-semibold text-black">
              Propriétaire
            </span>
            <select
              value={owner}
              onChange={(event) => setOwner(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
            >
              <option value="">Tous les propriétaires</option>
              {users.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.full_name}
                  {member.is_active ? "" : " (désactivé)"}
                </option>
              ))}
            </select>
          </label>
        ) : (
          !writable && (
            <label className="block sm:w-56">
              <span className="mb-1 block text-sm font-semibold text-black">
                Propriétaire (ID)
              </span>
              <input
                type="number"
                min={1}
                value={owner}
                onChange={(event) => setOwner(event.target.value)}
                placeholder="Tous les propriétaires"
                className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              />
            </label>
          )
        )}

        <label className="flex items-center gap-2 pb-2 text-sm font-semibold text-black">
          <input
            type="checkbox"
            checked={overdue}
            onChange={(event) => setOverdue(event.target.checked)}
            className="h-4 w-4"
          />
          En retard uniquement
        </label>
      </div>

      {error && (
        <p role="alert" className="text-red-900">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-black">Chargement des actions…</p>
      ) : actions.length === 0 ? (
        <p className="rounded-2xl border border-blue-100 bg-white p-6 text-black shadow-sm">
          Aucune action ne correspond à ces filtres.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-blue-100 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-blue-100 text-left text-sm">
            <thead className="bg-blue-50 text-black">
              <tr>
                <th className="px-4 py-3">Client</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Échéance</th>
                <th className="px-4 py-3">Créée le</th>
                <th className="px-4 py-3">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-blue-100 text-black">
              {actions.map((action) => {
                const overdueAction = isActionOverdue(action);
                return (
                  <tr key={action.id}>
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/customers/${action.customer_id}`}
                        className="text-blue-800 underline underline-offset-4 hover:text-blue-950"
                      >
                        Client #{action.customer_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      {ACTION_TYPE_LABELS[action.action_type]}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${ACTION_STATUS_CLASSES[action.status]}`}
                      >
                        {ACTION_STATUS_LABELS[action.status]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={overdueAction ? "font-semibold text-red-900" : ""}
                      >
                        {formatActionDate(action.due_date)}
                        {overdueAction ? " (en retard)" : ""}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {formatActionDateTime(action.created_at)}
                    </td>
                    <td className="max-w-xs px-4 py-3">
                      <span className="line-clamp-2">{action.note || "—"}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
