import type {
  ActionStatus,
  ActionType,
  CustomerAction,
  RetentionStatus,
} from "./types";

export const RETENTION_STATUS_LABELS: Record<RetentionStatus, string> = {
  none: "Non suivi",
  to_contact: "À contacter",
  contacted: "Contacté",
  retained: "Retenu",
  ignored: "Ignoré",
};

export const RETENTION_STATUS_OPTIONS: RetentionStatus[] = [
  "none",
  "to_contact",
  "contacted",
  "retained",
  "ignored",
];

export const ACTION_TYPE_LABELS: Record<ActionType, string> = {
  call: "Appel",
  email: "Email",
  discount: "Remise",
  onboarding: "Onboarding",
  other: "Autre",
};

export const ACTION_TYPE_OPTIONS: ActionType[] = [
  "call",
  "email",
  "discount",
  "onboarding",
  "other",
];

export const ACTION_STATUS_LABELS: Record<ActionStatus, string> = {
  todo: "À faire",
  in_progress: "En cours",
  done: "Fait",
  cancelled: "Annulé",
};

export const ACTION_STATUS_OPTIONS: ActionStatus[] = [
  "todo",
  "in_progress",
  "done",
  "cancelled",
];

export const ACTION_STATUS_CLASSES: Record<ActionStatus, string> = {
  todo: "bg-slate-200 text-slate-800",
  in_progress: "bg-blue-100 text-blue-900",
  done: "bg-green-100 text-green-900",
  cancelled: "bg-red-100 text-red-900",
};

/** Date locale au format ISO (YYYY-MM-DD), sans décalage UTC. */
export function todayIsoDate(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

export function formatActionDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("fr-FR", { dateStyle: "medium" });
}

export function formatActionDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("fr-FR", { dateStyle: "medium" });
}

export function isActionOverdue(
  action: Pick<CustomerAction, "due_date" | "status">,
): boolean {
  if (!action.due_date) return false;
  if (action.status !== "todo" && action.status !== "in_progress") return false;
  return action.due_date < todayIsoDate();
}
