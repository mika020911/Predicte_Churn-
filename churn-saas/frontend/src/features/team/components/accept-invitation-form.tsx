"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";
import {
  PASSWORD_HELP,
  PASSWORD_MAX_LENGTH,
  passwordRuleError,
} from "@/features/auth/password";
import { previewInvitation } from "../api/team-api";
import type { InvitationPreview } from "../types";

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrateur",
  analyst: "Analyste",
  viewer: "Lecture seule",
};

export function AcceptInvitationForm() {
  const { acceptInvitation } = useAuth();

  const [token, setToken] = useState("");
  const [preview, setPreview] = useState<InvitationPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const invitationToken = searchParams.get("token") ?? "";

    // Retire le jeton de la barre d'adresse et de l'historique du navigateur.
    window.history.replaceState({}, "", window.location.pathname);

    setToken(invitationToken);

    if (!invitationToken) {
      setPreviewError("Le lien ne contient pas de jeton d’invitation.");
      return;
    }

    let cancelled = false;
    previewInvitation(invitationToken)
      .then((data) => {
        if (!cancelled) {
          setPreview(data);
          setFullName("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setPreviewError(
            err instanceof Error
              ? err.message
              : "L’invitation est invalide, expirée ou déjà utilisée.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!token) {
      setError("Le lien ne contient pas de jeton d’invitation.");
      return;
    }

    if (password !== confirmation) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }

    const passwordError = passwordRuleError(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (!fullName.trim()) {
      setError("Renseigne ton nom complet.");
      return;
    }

    setLoading(true);
    try {
      await acceptInvitation({
        token,
        full_name: fullName.trim(),
        password,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "L’invitation n’a pas pu être acceptée.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-white p-6 text-black">
      <section className="w-full max-w-md space-y-5 rounded-xl border border-slate-300 bg-white p-8">
        <h1 className="text-2xl font-bold text-black">Rejoindre l’équipe</h1>

        {previewError && (
          <p role="alert" className="text-red-900">
            {previewError}
          </p>
        )}

        {preview && (
          <p className="text-black">
            <strong>{preview.organization_name}</strong> t’invite avec le rôle{" "}
            <strong>{ROLE_LABELS[preview.role] ?? preview.role}</strong> (
            {preview.email}).
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block font-medium text-black">
              Nom complet
            </span>
            <input
              type="text"
              required
              maxLength={255}
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              autoComplete="name"
            />
          </label>

          <label className="block">
            <span className="mb-1 block font-medium text-black">
              Mot de passe
            </span>
            <input
              type="password"
              required
              minLength={12}
              maxLength={PASSWORD_MAX_LENGTH}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              autoComplete="new-password"
            />
            <span className="mt-1 block text-xs text-black">
              {PASSWORD_HELP}
            </span>
          </label>

          <label className="block">
            <span className="mb-1 block font-medium text-black">
              Confirmer le mot de passe
            </span>
            <input
              type="password"
              required
              minLength={12}
              maxLength={PASSWORD_MAX_LENGTH}
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              autoComplete="new-password"
            />
          </label>

          {error && (
            <p role="alert" className="rounded-md bg-red-50 p-3 text-red-900">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !token || preview === null}
            className="w-full rounded-md bg-blue-700 px-4 py-2 font-semibold text-white hover:bg-blue-800 disabled:opacity-50"
          >
            {loading ? "Création du compte…" : "Créer mon compte"}
          </button>
        </form>

        <Link href="/auth/login" className="text-blue-800 underline">
          J’ai déjà un compte
        </Link>
      </section>
    </main>
  );
}
