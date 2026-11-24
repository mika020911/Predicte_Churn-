"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";
import {
  PASSWORD_HELP,
  PASSWORD_MAX_LENGTH,
  passwordRuleError,
} from "@/features/auth/password";

export function RegisterForm() {
  const { register } = useAuth();

  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const passwordError = passwordRuleError(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setLoading(true);

    try {
      await register({
        full_name: fullName,
        organization_name: organizationName,
        email,
        password,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible de créer le compte.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-white p-4 text-black sm:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl overflow-hidden rounded-[2rem] border border-blue-100 bg-white shadow-2xl sm:min-h-[calc(100vh-4rem)] lg:grid-cols-2">
        {/* Image réservée à la création de compte */}
        <section className="relative hidden min-h-[700px] overflow-hidden lg:block">
          <img
            src="/images/login_image.png"
            alt="Illustration ChurnSight"
            className="absolute inset-0 h-full w-full object-cover"
          />

          <div className="absolute inset-0 bg-blue-950/45" />

          <div className="relative z-10 flex h-full flex-col justify-between p-10 xl:p-14">
            <img
              src="/images/CHurnSight.gif"
              alt="ChurnSight"
              className="h-20 w-20 rounded-2xl bg-white object-contain p-2"
            />

            <div className="max-w-lg text-white">
              <p className="mb-4 inline-flex rounded-full border border-white/50 px-4 py-2 text-sm font-semibold">
                Bienvenue sur ChurnSight
              </p>

              <h1 className="text-4xl font-bold leading-tight xl:text-5xl">
                Donnez à votre équipe les moyens d’agir plus tôt.
              </h1>

              <p className="mt-6 text-lg leading-8 text-white">
                Créez votre espace organisation pour importer vos données et
                explorer les risques de départ de vos clients.
              </p>
            </div>

            <p className="text-sm text-white">
              ChurnSight — prédiction et compréhension du risque client
            </p>
          </div>
        </section>

        {/* Formulaire d’inscription */}
        <section className="flex items-center justify-center px-5 py-10 sm:px-10 lg:px-12 xl:px-16">
          <div className="w-full max-w-md">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <img
                src="/images/CHurnSight.gif"
                alt="ChurnSight"
                className="h-14 w-14 rounded-xl border border-blue-100 object-contain"
              />
              <span className="text-xl font-bold text-black">ChurnSight</span>
            </div>

            <div className="mb-7">
              <p className="mb-3 font-semibold text-blue-800">
                Créez votre espace
              </p>
              <h2 className="text-3xl font-bold tracking-tight text-black sm:text-4xl">
                Créer un compte
              </h2>
              <p className="mt-3 leading-6 text-black">
                Inscrivez votre organisation pour commencer.
              </p>
            </div>

            {error && (
              <div
                role="alert"
                className="mb-5 rounded-xl border border-red-300 bg-red-50 p-4 text-red-900"
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-black">
                  Nom complet
                </span>
                <input
                  type="text"
                  required
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Ex. Amina Randria"
                  className="w-full rounded-xl border border-blue-200 bg-white px-4 py-3 text-black outline-none placeholder:text-black focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-black">
                  Nom de l’organisation
                </span>
                <input
                  type="text"
                  required
                  autoComplete="organization"
                  value={organizationName}
                  onChange={(event) => setOrganizationName(event.target.value)}
                  placeholder="Ex. Acme"
                  className="w-full rounded-xl border border-blue-200 bg-white px-4 py-3 text-black outline-none placeholder:text-black focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-black">
                  Adresse email
                </span>
                <div className="relative">
                  <img
                    src="/icons/email.png"
                    alt=""
                    aria-hidden="true"
                    className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 object-contain"
                  />
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="nom@entreprise.com"
                    className="w-full rounded-xl border border-blue-200 bg-white py-3 pl-12 pr-4 text-black outline-none placeholder:text-black focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
                  />
                </div>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-black">
                  Mot de passe
                </span>
                <input
                  type="password"
                  required
                  minLength={12}
                  maxLength={PASSWORD_MAX_LENGTH}
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Au moins 12 caractères"
                  className="w-full rounded-xl border border-blue-200 bg-white px-4 py-3 text-black outline-none placeholder:text-black focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
                />
                <span className="mt-1 block text-xs text-black">
                  {PASSWORD_HELP}
                </span>
              </label>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-blue-700 px-5 py-3.5 font-semibold text-white shadow-lg shadow-blue-700/20 transition hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Création en cours…" : "Créer mon compte"}
              </button>
            </form>

            <p className="mt-7 text-center text-black">
              Vous avez déjà un compte ?{" "}
              <Link
                href="/auth/login"
                className="font-semibold text-blue-800 underline underline-offset-4 hover:text-blue-950"
              >
                Se connecter
              </Link>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}