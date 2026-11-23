"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { canManageTeam } from "@/features/auth/permissions";
import type { Role } from "@/features/auth/types";
import {
  createInvitation,
  deactivateMember,
  getInvitations,
  getMembers,
  resendInvitation,
  revokeInvitation,
  updateMember,
} from "../api/team-api";
import type { Invitation, InvitationStatus, Member } from "../types";

const ROLE_LABELS: Record<Role, string> = {
  admin: "Administrateur",
  analyst: "Analyste",
  viewer: "Lecture seule",
};

const ROLE_OPTIONS: Role[] = ["admin", "analyst", "viewer"];

const STATUS_LABELS: Record<InvitationStatus, string> = {
  pending: "En attente",
  accepted: "Acceptée",
  expired: "Expirée",
  revoked: "Révoquée",
};

const STATUS_CLASSES: Record<InvitationStatus, string> = {
  pending: "bg-blue-100 text-blue-900",
  accepted: "bg-green-100 text-green-900",
  expired: "bg-orange-100 text-orange-900",
  revoked: "bg-slate-200 text-slate-800",
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("fr-FR", { dateStyle: "medium" });
}

export function TeamManagement() {
  const { token, user, loading: authLoading } = useAuth();
  const allowed = canManageTeam(user?.role);

  const [members, setMembers] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<Role>("analyst");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [createdInvitation, setCreatedInvitation] = useState<Invitation | null>(
    null,
  );
  const [copied, setCopied] = useState(false);

  const loadTeam = useCallback(async () => {
    if (!token || !allowed) return;
    setLoading(true);
    setError(null);
    try {
      const [membersData, invitationsData] = await Promise.all([
        getMembers(token),
        getInvitations(token),
      ]);
      setMembers(membersData);
      setInvitations(invitationsData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger l’équipe.",
      );
    } finally {
      setLoading(false);
    }
  }, [token, allowed]);

  useEffect(() => {
    if (authLoading) return;
    if (!token) {
      setLoading(false);
      setError("Connecte-toi pour gérer l’équipe.");
      return;
    }
    if (!allowed) {
      setLoading(false);
      return;
    }
    void loadTeam();
  }, [authLoading, token, allowed, loadTeam]);

  async function handleRoleChange(member: Member, role: Role) {
    if (!token) return;
    setBusyId(`member-${member.id}`);
    setError(null);
    try {
      const updated = await updateMember(token, member.id, { role });
      setMembers((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Modification refusée.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggleActive(member: Member) {
    if (!token) return;
    setBusyId(`member-${member.id}`);
    setError(null);
    try {
      const updated = member.is_active
        ? await deactivateMember(token, member.id)
        : await updateMember(token, member.id, { is_active: true });
      setMembers((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Modification refusée.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleResend(invitation: Invitation) {
    if (!token) return;
    setBusyId(`invitation-${invitation.id}`);
    setError(null);
    try {
      const updated = await resendInvitation(token, invitation.id);
      setInvitations((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setCreatedInvitation(updated);
      setCopied(false);
      setModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Renvoi impossible.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleRevoke(invitation: Invitation) {
    if (!token) return;
    setBusyId(`invitation-${invitation.id}`);
    setError(null);
    try {
      const updated = await revokeInvitation(token, invitation.id);
      setInvitations((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Révocation impossible.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setInviting(true);
    setInviteError(null);
    try {
      const invitation = await createInvitation(token, {
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInvitations((current) => [invitation, ...current]);
      setCreatedInvitation(invitation);
      setCopied(false);
      setInviteEmail("");
      setInviteRole("analyst");
    } catch (err) {
      setInviteError(
        err instanceof Error ? err.message : "Invitation impossible.",
      );
    } finally {
      setInviting(false);
    }
  }

  async function copyLink() {
    if (!createdInvitation?.invite_url) return;
    try {
      await navigator.clipboard.writeText(createdInvitation.invite_url);
      setCopied(true);
    } catch {
      setInviteError("Copie impossible : sélectionne le lien manuellement.");
    }
  }

  function closeModal() {
    setModalOpen(false);
    setCreatedInvitation(null);
    setInviteError(null);
    setCopied(false);
  }

  if (authLoading) {
    return <p className="text-black">Chargement…</p>;
  }

  if (!allowed) {
    return (
      <section className="rounded-2xl border border-blue-100 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-black">Équipe</h1>
        <p role="alert" className="mt-3 text-red-900">
          Cette page est réservée aux administrateurs.
        </p>
      </section>
    );
  }

  const pendingInvitations = invitations.filter(
    (invitation) => invitation.status === "pending",
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-black">Équipe</h1>
          <p className="mt-1 text-black">
            Membres de l’organisation, rôles et invitations en attente.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setCreatedInvitation(null);
            setInviteError(null);
            setModalOpen(true);
          }}
          className="h-fit rounded-xl bg-blue-900 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-950"
        >
          Inviter un membre
        </button>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800"
        >
          {error}
        </p>
      )}

      <section className="space-y-3 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">Membres</h2>
        {loading ? (
          <p className="text-black">Chargement des membres…</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-blue-100">
            <table className="min-w-full divide-y divide-blue-100 text-left text-sm">
              <thead className="bg-blue-50 text-black">
                <tr>
                  <th className="px-4 py-3">Nom</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Rôle</th>
                  <th className="px-4 py-3">Statut</th>
                  <th className="px-4 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-100 text-black">
                {members.map((member) => {
                  const isSelf = member.id === user?.id;
                  return (
                    <tr key={member.id}>
                      <td className="px-4 py-3 font-semibold">
                        {member.full_name}
                        {isSelf && (
                          <span className="ml-2 text-xs font-normal text-blue-900">
                            (vous)
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">{member.email}</td>
                      <td className="px-4 py-3">
                        <select
                          aria-label={`Rôle de ${member.full_name}`}
                          value={member.role}
                          disabled={isSelf || busyId === `member-${member.id}`}
                          onChange={(event) =>
                            void handleRoleChange(
                              member,
                              event.target.value as Role,
                            )
                          }
                          className="rounded-md border border-blue-200 px-2 py-1 text-black disabled:opacity-60"
                        >
                          {ROLE_OPTIONS.map((role) => (
                            <option key={role} value={role}>
                              {ROLE_LABELS[role]}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${
                            member.is_active
                              ? "bg-green-100 text-green-900"
                              : "bg-slate-200 text-slate-800"
                          }`}
                        >
                          {member.is_active ? "Actif" : "Désactivé"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => void handleToggleActive(member)}
                          disabled={isSelf || busyId === `member-${member.id}`}
                          className="rounded-md border border-blue-200 px-3 py-1 text-xs font-semibold text-blue-900 hover:bg-blue-50 disabled:opacity-50"
                        >
                          {member.is_active ? "Désactiver" : "Réactiver"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="space-y-3 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-black">
          Invitations en attente
        </h2>
        {pendingInvitations.length === 0 ? (
          <p className="text-black">Aucune invitation en attente.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-blue-100">
            <table className="min-w-full divide-y divide-blue-100 text-left text-sm">
              <thead className="bg-blue-50 text-black">
                <tr>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Rôle</th>
                  <th className="px-4 py-3">Expire le</th>
                  <th className="px-4 py-3">Statut</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-100 text-black">
                {pendingInvitations.map((invitation) => (
                  <tr key={invitation.id}>
                    <td className="px-4 py-3">{invitation.email}</td>
                    <td className="px-4 py-3">
                      {ROLE_LABELS[invitation.role]}
                    </td>
                    <td className="px-4 py-3">
                      {formatDate(invitation.expires_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${
                          STATUS_CLASSES[invitation.status]
                        }`}
                      >
                        {STATUS_LABELS[invitation.status]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => void handleResend(invitation)}
                          disabled={
                            busyId === `invitation-${invitation.id}`
                          }
                          className="rounded-md border border-blue-200 px-3 py-1 text-xs font-semibold text-blue-900 hover:bg-blue-50 disabled:opacity-50"
                        >
                          Renvoyer
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleRevoke(invitation)}
                          disabled={
                            busyId === `invitation-${invitation.id}`
                          }
                          className="rounded-md border border-red-200 px-3 py-1 text-xs font-semibold text-red-900 hover:bg-red-50 disabled:opacity-50"
                        >
                          Révoquer
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-blue-950/40 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="invite-title"
            className="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-xl"
          >
            <div className="flex items-start justify-between gap-4">
              <h2 id="invite-title" className="text-xl font-bold text-black">
                {createdInvitation ? "Invitation créée" : "Inviter un membre"}
              </h2>
              <button
                type="button"
                onClick={closeModal}
                aria-label="Fermer"
                className="rounded-md px-2 py-1 text-lg font-bold text-black hover:bg-blue-50"
              >
                ×
              </button>
            </div>

            {createdInvitation ? (
              <div className="space-y-3">
                <p className="text-sm text-black">
                  Invitation pour <strong>{createdInvitation.email}</strong>{" "}
                  avec le rôle{" "}
                  <strong>{ROLE_LABELS[createdInvitation.role]}</strong>.
                </p>
                <p className="text-sm text-black">
                  {createdInvitation.email_sent
                    ? "L’email d’invitation a été envoyé."
                    : "L’email n’a pas pu être envoyé : transmets ce lien manuellement."}
                </p>
                <p className="text-xs text-orange-900">
                  Ce lien ne sera plus affiché : copie-le maintenant.
                </p>
                {createdInvitation.invite_url && (
                  <>
                    <code className="block break-all rounded-md bg-blue-50 p-3 text-xs text-black">
                      {createdInvitation.invite_url}
                    </code>
                    <button
                      type="button"
                      onClick={() => void copyLink()}
                      className="rounded-md bg-blue-900 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-950"
                    >
                      {copied ? "Lien copié ✓" : "Copier le lien"}
                    </button>
                  </>
                )}
                {inviteError && (
                  <p role="alert" className="text-sm text-red-900">
                    {inviteError}
                  </p>
                )}
              </div>
            ) : (
              <form onSubmit={handleInvite} className="space-y-4">
                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-black">
                    Email
                  </span>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(event) => setInviteEmail(event.target.value)}
                    className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
                    placeholder="prenom.nom@entreprise.com"
                  />
                </label>

                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-black">
                    Rôle
                  </span>
                  <select
                    value={inviteRole}
                    onChange={(event) =>
                      setInviteRole(event.target.value as Role)
                    }
                    className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
                  >
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {ROLE_LABELS[role]}
                      </option>
                    ))}
                  </select>
                </label>

                {inviteError && (
                  <p role="alert" className="text-sm text-red-900">
                    {inviteError}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={inviting}
                  className="w-full rounded-md bg-blue-900 px-4 py-2 font-semibold text-white hover:bg-blue-950 disabled:opacity-50"
                >
                  {inviting ? "Envoi…" : "Envoyer l’invitation"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
