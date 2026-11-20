import type { RiskSettings, RiskSettingsUpdate } from "../types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function errorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;

  if (typeof detail === "string") return detail;

  // Erreur de validation FastAPI : detail est une liste d'objets { msg, loc... }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : null,
      )
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) return messages.join(" ");
  }

  return fallback;
}

export async function getRiskSettings(token: string): Promise<RiskSettings> {
  const response = await fetch(`${API_URL}/risk-settings`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      errorMessage(body, "Impossible de charger les seuils de risque."),
    );
  }

  return response.json();
}

export async function updateRiskSettings(
  token: string,
  payload: RiskSettingsUpdate,
): Promise<RiskSettings> {
  const response = await fetch(`${API_URL}/risk-settings`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      errorMessage(body, "Impossible d’enregistrer les seuils de risque."),
    );
  }

  return response.json();
}
