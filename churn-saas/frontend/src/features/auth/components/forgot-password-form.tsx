"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { requestPasswordReset } from "../api/auth-api";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);

    try {
      const result = await requestPasswordReset(email);
      setMessage(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Une erreur est survenue.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-white p-6 text-black">
      <section className="w-full max-w-md space-y-5 rounded-xl border border-slate-300 bg-white p-8">
        <h1 className="text-2xl font-bold text-black">
          Mot de passe oublié
        </h1>

        <p className="text-black">
          Saisis l’adresse email associée à ton compte. Si un compte existe,
          un lien de réinitialisation sera envoyé.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block font-medium text-black">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-md border border-slate-400 px-3 py-2 text-black"
              autoComplete="email"
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
            disabled={loading}
            className="w-full rounded-md bg-blue-700 px-4 py-2 font-semibold text-white hover:bg-blue-800 disabled:opacity-50"
          >
            {loading ? "Envoi en cours…" : "Envoyer le lien"}
          </button>
        </form>

        <Link href="/auth/login" className="text-blue-800 underline">
          Retour à la connexion
        </Link>
      </section>
    </main>
  );
}