"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { submitNewPassword } from "../api/auth-api";

export function ResetPasswordForm() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    setToken(searchParams.get("token") ?? "");
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);

    if (!token) {
      setError("Le lien ne contient pas de jeton de réinitialisation.");
      return;
    }

    if (password !== confirmation) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }

    if (password.length < 12) {
      setError("Le mot de passe doit contenir au moins 12 caractères.");
      return;
    }

    setLoading(true);

    try {
      const result = await submitNewPassword(token, password);
      setMessage(result);
      setPassword("");
      setConfirmation("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Le lien est invalide ou expiré.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-white p-6 text-black">
      <section className="w-full max-w-md space-y-5 rounded-xl border border-slate-300 bg-white p-8">
        <h1 className="text-2xl font-bold text-black">
          Choisir un nouveau mot de passe
        </h1>

        {!token && (
          <p role="alert" className="text-red-900">
            Aucun jeton trouvé dans le lien. Demande un nouveau lien de
            réinitialisation.
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block font-medium text-black">
              Nouveau mot de passe
            </span>
            <input
              type="password"
              required
              minLength={12}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              autoComplete="new-password"
            />
          </label>

          <label className="block">
            <span className="mb-1 block font-medium text-black">
              Confirmer le mot de passe
            </span>
            <input
              type="password"
              required
              minLength={12}
              maxLength={128}
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              autoComplete="new-password"
            />
          </label>

          {message && (
            <p role="status" className="rounded-md bg-green-50 p-3 text-green-900">
              {message}
            </p>
          )}

          {error && (
            <p role="alert" className="rounded-md bg-red-50 p-3 text-red-900">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !token}
            className="w-full rounded-md bg-blue-700 px-4 py-2 font-semibold text-white hover:bg-blue-800 disabled:opacity-50"
          >
            {loading ? "Mise à jour…" : "Réinitialiser le mot de passe"}
          </button>
        </form>

        {message && (
          <Link href="/auth/login" className="text-blue-800 underline">
            Aller à la connexion
          </Link>
        )}
      </section>
    </main>
  );
}