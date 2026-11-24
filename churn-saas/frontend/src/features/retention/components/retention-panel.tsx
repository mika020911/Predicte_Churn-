"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { canWrite } from "@/features/auth/permissions";
import { featureLabel } from "@/features/customers/risk";
import {
  createCustomerAction,
  getCustomerActions,
  getRetentionUsers,
  updateCustomerRetention,
} from "../api/retention-api";
import {
  ACTION_TYPE_LABELS,
  ACTION_TYPE_OPTIONS,
  RETENTION_STATUS_LABELS,
  RETENTION_STATUS_OPTIONS,
} from "../labels";
import type {
  ActionType,
  CustomerAction,
  RetentionStatus,
  RetentionUser,
  SuggestedAction,
} from "../types";
import { ActionTimeline } from "./action-timeline";

type RetentionPanelProps = {
  customerId: number;
  retentionStatus: RetentionStatus;
  ownerUserId: number | null;
  suggestedActions: SuggestedAction[];
};

export function RetentionPanel({
  customerId,
  retentionStatus,
  ownerUserId,
  suggestedActions,
}: RetentionPanelProps) {
  const { token, user } = useAuth();
  const writable = canWrite(user?.role);

  const [status, setStatus] = useState<RetentionStatus>(retentionStatus);
  const [ownerId, setOwnerId] = useState(
    ownerUserId ? String(ownerUserId) : "",
  );
  const [users, setUsers] = useState<RetentionUser[]>([]);
  const [actions, setActions] = useState<CustomerAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<"status" | "owner" | "create" | null>(
    null,
  );
  const [busySuggestion, setBusySuggestion] = useState<number | null>(null);

  const [actionType, setActionType] = useState<ActionType>("call");
  const [note, setNote] = useState("");
  const [dueDate, setDueDate] = useState("");

  useEffect(() => {
    setStatus(retentionStatus);
  }, [retentionStatus]);

  useEffect(() => {
    setOwnerId(ownerUserId ? String(ownerUserId) : "");
  }, [ownerUserId]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    setLoading(true);
    getCustomerActions(token, customerId)
      .then((data) => {
        if (!cancelled) setActions(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger les actions.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    if (writable) {
      getRetentionUsers(token)
        .then((data) => {
          if (!cancelled) setUsers(data);
        })
        .catch(() => {
          // Lecture des membres réservée aux admins/analystes : le sélecteur
          // reste vide sans bloquer la fiche.
        });
    }

    return () => {
      cancelled = true;
    };
  }, [token, customerId, writable]);

  const ownerLabel = ownerId
    ? (users.find((member) => member.id === Number(ownerId))?.full_name ??
      `Utilisateur #${ownerId}`)
    : "Non attribué";

  async function handleStatusChange(nextStatus: RetentionStatus) {
    if (!token || !writable) return;
    setSaving("status");
    setError(null);
    try {
      const updated = await updateCustomerRetention(token, customerId, {
        retention_status: nextStatus,
      });
      setStatus(updated.retention_status);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Changement de statut impossible.",
      );
    } finally {
      setSaving(null);
    }
  }

  async function handleOwnerChange(value: string) {
    if (!token || !writable) return;
    setSaving("owner");
    setError(null);
    try {
      const updated = await updateCustomerRetention(token, customerId, {
        owner_user_id: value ? Number(value) : null,
      });
      setOwnerId(updated.owner_user_id ? String(updated.owner_user_id) : "");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Changement de propriétaire impossible.",
      );
    } finally {
      setSaving(null);
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !writable) return;
    setSaving("create");
    setError(null);
    try {
      const created = await createCustomerAction(token, customerId, {
        action_type: actionType,
        status: "todo",
        note: note.trim() ? note.trim() : null,
        due_date: dueDate || null,
      });
      setActions((current) => [created, ...current]);
      setNote("");
      setDueDate("");
      setActionType("call");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Ajout de l’action impossible.",
      );
    } finally {
      setSaving(null);
    }
  }

  async function handleSuggested(suggestion: SuggestedAction, index: number) {
    if (!token || !writable) return;
    setBusySuggestion(index);
    setError(null);
    try {
      const created = await createCustomerAction(token, customerId, {
        action_type: suggestion.action_type,
        status: "todo",
        note: suggestion.label,
        due_date: null,
      });
      setActions((current) => [created, ...current]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Ajout de l’action impossible.",
      );
    } finally {
      setBusySuggestion(null);
    }
  }

  function handleActionUpdated(updated: CustomerAction) {
    setActions((current) =>
      current.map((action) => (action.id === updated.id ? updated : action)),
    );
  }

  return (
    <section className="space-y-5 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-bold text-black">Suivi de rétention</h2>
        <p className="mt-1 text-sm text-black">
          Statut, propriétaire du suivi et journal des actions menées.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-sm font-semibold text-black">
            Statut de rétention
          </p>
          {writable ? (
            <select
              value={status}
              onChange={(event) =>
                void handleStatusChange(event.target.value as RetentionStatus)
              }
              disabled={saving === "status"}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black disabled:opacity-50"
            >
              {RETENTION_STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {RETENTION_STATUS_LABELS[option]}
                </option>
              ))}
            </select>
          ) : (
            <span className="inline-flex rounded-full bg-blue-100 px-3 py-1 text-sm font-semibold text-blue-900">
              {RETENTION_STATUS_LABELS[status]}
            </span>
          )}
        </div>

        <div>
          <p className="mb-1 text-sm font-semibold text-black">Propriétaire</p>
          {writable ? (
            <select
              value={ownerId}
              onChange={(event) => void handleOwnerChange(event.target.value)}
              disabled={saving === "owner"}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black disabled:opacity-50"
            >
              <option value="">Non attribué</option>
              {users.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.full_name}
                  {member.is_active ? "" : " (désactivé)"}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-black">{ownerLabel}</p>
          )}
        </div>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-900">
          {error}
        </p>
      )}

      <div>
        <h3 className="text-lg font-bold text-black">Actions suggérées</h3>
        {suggestedActions.length === 0 ? (
          <p className="mt-2 text-sm text-black">
            Aucune suggestion pour ce client.
          </p>
        ) : (
          <ul className="mt-3 space-y-2">
            {suggestedActions.map((suggestion, index) => (
              <li
                key={`${suggestion.action_type}-${index}`}
                className="flex flex-wrap items-center gap-3 rounded-xl bg-blue-50 px-4 py-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-black">
                    {suggestion.label}
                  </p>
                  <p className="mt-1 text-xs text-black">
                    {ACTION_TYPE_LABELS[suggestion.action_type]}
                    {suggestion.feature
                      ? ` · ${featureLabel(suggestion.feature)}`
                      : ""}
                    {" · impact "}
                    {suggestion.impact > 0 ? "+" : ""}
                    {suggestion.impact.toFixed(2)}
                  </p>
                </div>
                {writable && (
                  <button
                    type="button"
                    onClick={() => void handleSuggested(suggestion, index)}
                    disabled={busySuggestion !== null}
                    className="rounded-md bg-blue-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-950 disabled:opacity-50"
                  >
                    {busySuggestion === index ? "Ajout…" : "Ajouter"}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {writable && (
        <form
          onSubmit={handleCreate}
          className="space-y-3 rounded-xl border border-blue-100 p-4"
        >
          <h3 className="text-lg font-bold text-black">Nouvelle action</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-black">
                Type d’action
              </span>
              <select
                value={actionType}
                onChange={(event) =>
                  setActionType(event.target.value as ActionType)
                }
                className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              >
                {ACTION_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {ACTION_TYPE_LABELS[option]}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-black">
                Échéance
              </span>
              <input
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
                className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              />
            </label>
          </div>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-black">
              Note
            </span>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              maxLength={4000}
              rows={2}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              placeholder="Contenu de l’action (optionnel)…"
            />
          </label>
          <button
            type="submit"
            disabled={saving === "create"}
            className="rounded-md bg-blue-900 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-950 disabled:opacity-50"
          >
            {saving === "create" ? "Ajout…" : "Ajouter l’action"}
          </button>
        </form>
      )}

      <div>
        <h3 className="text-lg font-bold text-black">
          Journal des actions
          {actions.length > 0 ? ` (${actions.length})` : ""}
        </h3>
        <div className="mt-3">
          {loading ? (
            <p className="text-sm text-black">Chargement des actions…</p>
          ) : (
            <ActionTimeline
              actions={actions}
              canWrite={writable}
              onUpdated={handleActionUpdated}
            />
          )}
        </div>
      </div>
    </section>
  );
}
