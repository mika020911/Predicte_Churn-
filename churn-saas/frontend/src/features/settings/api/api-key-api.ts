import type { ApiKeyRotateRead, ApiKeyStatus } from "../types";

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

export async function getApiKeyInfo(token: string): Promise<ApiKeyStatus> {
  const response = await fetch(`${API_URL}/settings/api-key`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      errorMessage(body, "Impossible de charger l’état de la clé API."),
    );
  }

  return response.json();
}

export async function rotateApiKey(token: string): Promise<ApiKeyRotateRead> {
  const response = await fetch(`${API_URL}/settings/api-key/rotate`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      errorMessage(body, "Impossible de générer la clé API."),
    );
  }

  return response.json();
}
