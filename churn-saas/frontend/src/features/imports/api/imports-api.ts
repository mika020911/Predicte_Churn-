import type { ImportBatch } from "../types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function uploadCsv(
  token: string,
  file: File,
): Promise<ImportBatch> {
  const formData = new FormData();
  formData.append("file", file);

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