import type { Role } from "@/features/auth/types";

export type InvitationStatus = "pending" | "accepted" | "expired" | "revoked";

export interface Member {
  id: number;
  organization_id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Invitation {
  id: number;
  email: string;
  role: Role;
  status: InvitationStatus;
  invited_by_user_id: number | null;
  expires_at: string;
  created_at: string;
  /** Renseigné uniquement à la création ou au renvoi. */
  invite_url: string | null;
  email_sent: boolean | null;
}

export interface InvitationCreatePayload {
  email: string;
  role: Role;
}

export interface MemberUpdatePayload {
  full_name?: string;
  role?: Role;
  is_active?: boolean;
}

export interface InvitationPreview {
  email: string;
  organization_name: string;
  role: Role;
  expires_at: string;
}

export interface AcceptInvitationPayload {
  token: string;
  full_name: string;
  password: string;
}
