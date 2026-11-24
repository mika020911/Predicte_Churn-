import type { TokenResponse } from "@/features/auth/types";
import type {
  AcceptInvitationPayload,
  Invitation,
  InvitationCreatePayload,
  InvitationPreview,
  Member,
  MemberUpdatePayload,
} from "../types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

function authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

async function request<T>(
  token: string,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...authHeaders(token),
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

export function getMembers(token: string): Promise<Member[]> {
  return request<Member[]>(token, "/users");
}

export function updateMember(
  token: string,
  userId: number,
  payload: MemberUpdatePayload,
): Promise<Member> {
  return request<Member>(token, `/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deactivateMember(
  token: string,
  userId: number,
): Promise<Member> {
  return request<Member>(token, `/users/${userId}`, { method: "DELETE" });
}

export function getInvitations(token: string): Promise<Invitation[]> {
  return request<Invitation[]>(token, "/users/invitations");
}

export function createInvitation(
  token: string,
  payload: InvitationCreatePayload,
): Promise<Invitation> {
  return request<Invitation>(token, "/users/invitations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resendInvitation(
  token: string,
  invitationId: number,
): Promise<Invitation> {
  return request<Invitation>(token, `/users/invitations/${invitationId}/resend`, {
    method: "POST",
  });
}

export function revokeInvitation(
  token: string,
  invitationId: number,
): Promise<Invitation> {
  return request<Invitation>(token, `/users/invitations/${invitationId}`, {
    method: "DELETE",
  });
}

export async function previewInvitation(
  token: string,
): Promise<InvitationPreview> {
  const response = await fetch(
    `${API_URL}/auth/invitations/preview?token=${encodeURIComponent(token)}`,
    { cache: "no-store" },
  );
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      errorMessage(body, "L’invitation est invalide, expirée ou déjà utilisée."),
    );
  }
  return body as InvitationPreview;
}

export async function acceptInvitationApi(
  payload: AcceptInvitationPayload,
): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/invitations/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(errorMessage(body, "L’invitation n’a pas pu être acceptée."));
  }
  return body as TokenResponse;
}
