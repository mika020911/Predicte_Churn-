import type {
  ActionFilters,
  CustomerAction,
  CustomerActionPayload,
  CustomerActionUpdatePayload,
  RetentionUpdatePayload,
  RetentionUpdateResponse,
  RetentionUser,
} from "../types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/** Extrait un message lisible d'une erreur FastAPI (chaîne ou validation). */
function errorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: unknown };
      if (typeof first?.msg === "string") return first.msg;
    }
  }
  return fallback;
}

async function request<T>(
  token: string,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
    cache: "no-store",
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(errorMessage(body, "L’opération a échoué."));
  }
  return body as T;
}

export function listActions(
  token: string,
  filters: ActionFilters = {},
): Promise<CustomerAction[]> {
  const query = new URLSearchParams();
  if (filters.status) query.set("status", filters.status);
  if (filters.owner) query.set("owner", String(filters.owner));
  if (filters.overdue) query.set("overdue", "true");
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<CustomerAction[]>(token, `/actions${suffix}`);
}

export function getCustomerActions(
  token: string,
  customerId: number,
): Promise<CustomerAction[]> {
  return request<CustomerAction[]>(token, `/customers/${customerId}/actions`);
}

export function createCustomerAction(
  token: string,
  customerId: number,
  payload: CustomerActionPayload,
): Promise<CustomerAction> {
  return request<CustomerAction>(token, `/customers/${customerId}/actions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCustomerAction(
  token: string,
  actionId: number,
  payload: CustomerActionUpdatePayload,
): Promise<CustomerAction> {
  return request<CustomerAction>(token, `/actions/${actionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateCustomerRetention(
  token: string,
  customerId: number,
  payload: RetentionUpdatePayload,
): Promise<RetentionUpdateResponse> {
  return request<RetentionUpdateResponse>(token, `/customers/${customerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getRetentionUsers(token: string): Promise<RetentionUser[]> {
  return request<RetentionUser[]>(token, "/users");
}
