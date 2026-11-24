const IMPORT_STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  processing: "En cours",
  completed: "Terminé",
  failed: "Échec",
  cancelled: "Annulé",
};

const IMPORT_STATUS_CLASSES: Record<string, string> = {
  pending: "bg-slate-100 text-slate-800",
  processing: "bg-blue-100 text-blue-900",
  completed: "bg-green-100 text-green-900",
  failed: "bg-red-100 text-red-900",
  cancelled: "bg-amber-100 text-amber-900",
};

export function importStatusLabel(status: string): string {
  return IMPORT_STATUS_LABELS[status] ?? status;
}

export function importStatusClass(status: string): string {
  return IMPORT_STATUS_CLASSES[status] ?? "bg-slate-100 text-slate-800";
}
