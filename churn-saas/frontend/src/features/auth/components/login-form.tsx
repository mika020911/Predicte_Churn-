"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";

export function LoginForm() {
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ email, password });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de se connecter.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-white p-4 text-black sm:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl overflow-hidden rounded-[2rem] border border-blue-100 bg-white shadow-2xl sm:min-h-[calc(100vh-4rem)] lg:grid-cols-2">
        {/* Panneau visuel */}
        <section className="relative hidden min-h-[680px] overflow-hidden lg:block">
<div
  aria-hidden="true"
  className="absolute inset-0 bg-gradient-to-br from-blue-950 via-blue-800 to-violet-800"
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
                Analyse intelligente du churn
              </p>

              <h1 className="text-4xl font-bold leading-tight xl:text-5xl">
                Anticipez les départs.
                <br />
                Renforcez vos relations clients.
              </h1>

              <p className="mt-6 max-w-md text-lg leading-8 text-white">
                Identifiez les clients à risque et comprenez les facteurs qui
                influencent leurs prédictions.
              </p>
            </div>

            <p className="text-sm text-white">
              ChurnSight — prédiction et compréhension du risque client
            </p>
          </div>
        </section>

        {/* Formulaire */}
        <section className="flex items-center justify-center px-5 py-10 sm:px-10 lg:px-12 xl:px-20">
          <div className="w-full max-w-md">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <img
                src="/images/CHurnSight.gif"
                alt="ChurnSight"
                className="h-14 w-14 rounded-xl border border-blue-100 object-contain"
              />
              <span className="text-xl font-bold text-black">ChurnSight</span>
            </div>

            <div className="mb-8">
              <p className="mb-3 font-semibold text-blue-800">
                Bienvenue sur ChurnSight
              </p>
              <h2 className="text-3xl font-bold tracking-tight text-black sm:text-4xl">
                Connectez-vous
              </h2>
              <p className="mt-3 leading-6 text-black">
                Accédez à votre espace d’analyse du risque client.
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

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label
                  htmlFor="email"
                  className="mb-2 block text-sm font-semibold text-black"
                >
                  Adresse email
                </label>

                <div className="relative">
                  <img
                    src="/icons/email.png"
                    alt=""
                    aria-hidden="true"
                    className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 object-contain"
                  />

                  <input
                    id="email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="nom@entreprise.com"
                    className="w-full rounded-xl border border-blue-200 bg-white py-3.5 pl-12 pr-4 text-black outline-none transition placeholder:text-black focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
                  />
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between gap-4">
                  <label
                    htmlFor="password"
                    className="text-sm font-semibold text-black"
                  >
                    Mot de passe
                  </label>

                  <Link
                    href="/auth/forgot-password"
                    className="text-sm font-semibold text-blue-800 underline underline-offset-4 hover:text-blue-950"
                  >
                    Mot de passe oublié ?
                  </Link>
                </div>

                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Saisissez votre mot de passe"
                    className="w-full rounded-xl border border-blue-200 bg-white py-3.5 pl-4 pr-12 text-black outline-none transition placeholder:text-black focus:border-blue-700 focus:ring-4 focus:ring-blue-100"
                  />

                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label={
                      showPassword
                        ? "Masquer le mot de passe"
                        : "Afficher le mot de passe"
                    }
                    aria-pressed={showPassword}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 focus:outline-none focus:ring-2 focus:ring-blue-700"
                  >
                    <img
                      src="/icons/oeil.png"
                      alt=""
                      aria-hidden="true"
                      className="h-6 w-6 object-contain"
                    />
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-blue-700 px-5 py-3.5 font-semibold text-white shadow-lg shadow-blue-700/20 transition hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Connexion en cours…" : "Se connecter"}
              </button>
            </form>

            <p className="mt-8 text-center text-black">
              Vous n’avez pas encore de compte ?{" "}
              <Link
                href="/auth/register"
                className="font-semibold text-blue-800 underline underline-offset-4 hover:text-blue-950"
              >
                Créer un compte
              </Link>
            </p>

            <p className="mt-10 text-center text-xs text-black">
              En vous connectant, vous accédez aux données de votre organisation.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}