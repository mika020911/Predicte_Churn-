"use client";

import { useState } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { updateCustomerAction } from "../api/retention-api";
import {
  ACTION_STATUS_CLASSES,
  ACTION_STATUS_LABELS,
  ACTION_TYPE_LABELS,
  formatActionDate,
  formatActionDateTime,
  isActionOverdue,
} from "../labels";
import type {
  ActionStatus,
  CustomerAction,
  CustomerActionUpdatePayload,
} from "../types";

type ActionRowProps = {
  action: CustomerAction;
  canWrite: boolean;
  onUpdated: (action: CustomerAction) => void;
};

function statusTransitions(
  status: ActionStatus,
): Array<{ label: string; status: ActionStatus }> {
  if (status === "todo") {
    return [
      { label: "Passer en cours", status: "in_progress" },
      { label: "Marquer fait", status: "done" },
      { label: "Annuler", status: "cancelled" },
    ];
  }
  if (status === "in_progress") {
    return [
      { label: "Marquer fait", status: "done" },
      { label: "Annuler", status: "cancelled" },
    ];
  }
  return [{ label: "Rouvrir", status: "todo" }];
}

function ActionRow({ action, canWrite, onUpdated }: ActionRowProps) {
  const { token } = useAuth();
  const [note, setNote] = useState(action.note ?? "");
  const [dueDate, setDueDate] = useState(action.due_date ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function patch(payload: CustomerActionUpdatePayload) {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await updateCustomerAction(token, action.id, payload);
      onUpdated(updated);
      setNote(updated.note ?? "");
      setDueDate(updated.due_date ?? "");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Mise à jour impossible.",
      );
    } finally {
      setBusy(false);
    }
  }

  const overdue = isActionOverdue(action);

  return (
    <li className="rounded-xl border border-blue-100 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold text-black">
          {ACTION_TYPE_LABELS[action.action_type]}
        </span>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${ACTION_STATUS_CLASSES[action.status]}`}
        >
          {ACTION_STATUS_LABELS[action.status]}
        </span>
        {overdue && (
          <span className="rounded-full bg-red-100 px-2.5 py-1 text-xs font-semibold text-red-900">
            En retard
          </span>
        )}
        <span className="ml-auto text-xs text-black">
          Créée le {formatActionDateTime(action.created_at)}
        </span>
      </div>

      <div className="mt-2 space-y-1 text-sm text-black">
        <p>Échéance : {formatActionDate(action.due_date)}</p>
        {action.completed_at && (
          <p>Terminée le {formatActionDateTime(action.completed_at)}</p>
        )}
      </div>

      {action.note && (
        <p className="mt-2 whitespace-pre-line text-sm text-black">
          {action.note}
        </p>
      )}

      {canWrite && (
        <div className="mt-3 space-y-3 border-t border-blue-100 pt-3">
          <div className="flex flex-wrap gap-2">
            {statusTransitions(action.status).map((transition) => (
              <button
                key={transition.status}
                type="button"
                onClick={() => void patch({ status: transition.status })}
                disabled={busy}
                className="rounded-md border border-blue-200 px-3 py-1 text-xs font-semibold text-blue-900 hover:bg-blue-50 disabled:opacity-50"
              >
                {transition.label}
              </button>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <label className="block">
              <span className="mb-1 block text-xs font-semibold text-black">
                Note
              </span>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                maxLength={4000}
                rows={2}
                className="w-full rounded-md border border-slate-400 px-3 py-2 text-sm text-black"
                placeholder="Compte rendu de l’action…"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-semibold text-black">
                Échéance
              </span>
              <input
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
                className="w-full rounded-md border border-slate-400 px-3 py-2 text-sm text-black"
              />
            </label>
          </div>

          <button
            type="button"
            onClick={() =>
              void patch({
                note: note.trim() ? note.trim() : null,
                due_date: dueDate || null,
              })
            }
            disabled={busy}
            className="rounded-md bg-blue-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-950 disabled:opacity-50"
          >
            {busy ? "Enregistrement…" : "Enregistrer la note et l’échéance"}
          </button>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-2 text-xs text-red-900">
          {error}
        </p>
      )}
    </li>
  );
}

type ActionTimelineProps = {
  actions: CustomerAction[];
  canWrite: boolean;
  onUpdated: (action: CustomerAction) => void;
};

export function ActionTimeline({
  actions,
  canWrite,
  onUpdated,
}: ActionTimelineProps) {
  if (actions.length === 0) {
    return (
      <p className="text-sm text-black">
        Aucune action enregistrée pour ce client.
      </p>
    );
  }

  return (
    <ol className="space-y-3">
      {actions.map((action) => (
        <ActionRow
          key={action.id}
          action={action}
          canWrite={canWrite}
          onUpdated={onUpdated}
        />
      ))}
    </ol>
  );
}
