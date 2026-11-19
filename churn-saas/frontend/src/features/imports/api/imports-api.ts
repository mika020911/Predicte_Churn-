import type { ImportBatch, ImportBatchSummary } from "../types";
import type { ImportPreview } from "../types";


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function previewCsv(
  token:string,
  file:File,
  mapping?: Record<string, string | null>,
):Promise<ImportPreview> {
    const formData = new FormData();
    formData.append("file", file);
    if (mapping) {
      formData.append("mapping", JSON.stringify(mapping));
    }

    const response =await fetch (`${API_URL}/imports/preview`, {
      method:"POST",
      headers:{
        Authorization: `Bearer ${token}`,
      },
      body:formData,
    });
    if (!response.ok){
      const body = await response.json().catch(()=> ({}));
      throw new Error(
        typeof body.detail === "string"
        ? body.detail
        : "Imposible de prévisualiser le fichier CSV."
      );
    }
    return response.json();
}

export async function saveColumnMapping(
  token:string,
  mapping: Record<string, string | null>,
  planOrder: string[] = [],
):Promise<void> {
  const response = await fetch(`${API_URL}/imports/mapping`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      column_mapping: mapping,
      contract_values: {},
      plan_order: planOrder,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Impossible d’enregistrer le mapping.",
    );
  }
}

export async function uploadCsv(
  token: string,
  file: File,
  mapping: Record<string, string | null>,
): Promise<ImportBatch> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mapping", JSON.stringify(mapping));

  const response = await fetch(`${API_URL}/imports/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      typeof body.detail === "string"
        ? body.detail
        : "L’import du fichier a échoué.";

    throw new Error(message);
  }

  return response.json();
}

//historique import

export async function getImportHistory(
  token: string,
): Promise<ImportBatchSummary[]> {
  const response = await fetch(`${API_URL}/imports/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Impossible de charger l’historique des imports.");
  }

  return response.json();
}

export async function getImportDetails(
  token: string,
  importId: number,
): Promise<ImportBatch> {
  const response = await fetch(`${API_URL}/imports/${importId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Impossible de charger le rapport d’import.",
    );
  }

  return response.json();
}