"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/context/auth-context";

const actions = [
  {
    number: "01",
    eyebrow: "Explorer",
    title: "Consulter les clients",
    description:
      "Rechercher un client, filtrer les niveaux de risque et consulter les facteurs associés.",
    href: "/dashboard/customers",
    linkLabel: "Voir les clients",
    color: "border-blue-200 bg-blue-50",
    numberColor: "bg-blue-700",
  },
  {
    number: "02",
    eyebrow: "Ajouter des données",
    title: "Importer un fichier CSV",
    description:
      "Prévisualiser un fichier, associer ses colonnes et consulter le rapport d’import.",
    href: "/dashboard/imports",
    linkLabel: "Lancer un import",
    color: "border-violet-200 bg-violet-50",
    numberColor: "bg-violet-700",
  },
  {
    number: "03",
    eyebrow: "Suivre",
    title: "Consulter l’historique",
    description:
      "Retrouver les imports précédents et ouvrir leurs rapports.",
    href: "/dashboard/imports/history",
    linkLabel: "Voir l’historique",
    color: "border-emerald-200 bg-emerald-50",
    numberColor: "bg-emerald-700",
  },
];

export default function DashboardPage() {
  const { user } = useAuth();

  const firstName = user?.full_name?.trim().split(/\s+/)[0];

  return (
    <main className="min-h-screen bg-white px-5 py-8 text-black sm:px-8 lg:px-12">
      <div className="mx-auto max-w-7xl space-y-10">
        {/* Bienvenue */}
        <section className="relative isolate overflow-hidden rounded-[2rem] bg-blue-950 px-6 py-10 text-white shadow-xl sm:px-10 sm:py-14">
          <div
            aria-hidden="true"
            className="absolute -right-16 -top-24 -z-10 h-80 w-80 rounded-full bg-blue-500/40 blur-3xl"
          />
          <div
            aria-hidden="true"
            className="absolute bottom-[-9rem] right-1/3 -z-10 h-72 w-72 rounded-full bg-violet-500/30 blur-3xl"
          />

          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-200">
              Espace de pilotage
            </p>

            <h1 className="mt-4 text-3xl font-bold leading-tight sm:text-5xl">
              Bonjour{firstName ? ` ${firstName}` : ""}.
              <br />
              <span className="text-blue-200">
                Que souhaitez-vous faire ?
              </span>
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-7 text-white sm:text-lg">
              Retrouvez vos clients, importez de nouvelles données et
              consultez les rapports de votre organisation.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/dashboard/customers"
                className="rounded-full bg-white px-6 py-3 font-semibold text-blue-950 transition hover:bg-blue-50"
              >
                Ouvrir les clients
              </Link>

              <Link
                href="/dashboard/imports"
                className="rounded-full border border-white/60 px-6 py-3 font-semibold text-white transition hover:bg-white/10"
              >
                Importer un CSV
              </Link>
            </div>
          </div>
        </section>

        {/* Raccourcis fonctionnels */}
        <section aria-labelledby="quick-actions-title">
          <div className="mb-6">
            <p className="font-semibold text-blue-800">Votre espace</p>
            <h2
              id="quick-actions-title"
              className="mt-2 text-2xl font-bold text-black sm:text-3xl"
            >
              Accès rapides
            </h2>
          </div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {actions.map((action) => (
              <article
                key={action.number}
                className={`flex min-h-72 flex-col rounded-3xl border p-6 sm:p-7 ${action.color}`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`inline-flex h-11 w-11 items-center justify-center rounded-2xl font-bold text-white ${action.numberColor}`}
                  >
                    {action.number}
                  </span>
                  <span className="text-sm font-semibold text-black">
                    {action.eyebrow}
                  </span>
                </div>

                <h3 className="mt-7 text-xl font-bold text-black">
                  {action.title}
                </h3>

                <p className="mt-3 flex-1 leading-7 text-black">
                  {action.description}
                </p>

                <Link
                  href={action.href}
                  className="mt-6 inline-flex w-fit items-center gap-2 font-bold text-blue-900 underline underline-offset-4 hover:text-blue-700"
                >
                  {action.linkLabel}
                  <span aria-hidden="true">→</span>
                </Link>
              </article>
            ))}
          </div>
        </section>

        {/* Repère sur le fonctionnement */}
        <section className="rounded-3xl border border-blue-100 bg-white p-6 shadow-sm sm:p-8">
          <p className="font-semibold text-blue-800">Comment commencer</p>
          <h2 className="mt-2 text-2xl font-bold text-black">
            Trois étapes pour démarrer
          </h2>

          <ol className="mt-6 grid gap-5 md:grid-cols-3">
            <li className="border-l-4 border-blue-700 pl-4">
              <p className="font-bold text-black">1. Préparez vos données</p>
              <p className="mt-2 leading-6 text-black">
                Utilisez le modèle CSV ou associez les colonnes de votre propre
                fichier.
              </p>
            </li>
            <li className="border-l-4 border-violet-700 pl-4">
              <p className="font-bold text-black">2. Importez le fichier</p>
              <p className="mt-2 leading-6 text-black">
                Prévisualisez les colonnes avant de confirmer l’import.
              </p>
            </li>
            <li className="border-l-4 border-emerald-700 pl-4">
              <p className="font-bold text-black">3. Analysez les résultats</p>
              <p className="mt-2 leading-6 text-black">
                Consultez la liste des clients, leurs scores et les facteurs
                associés.
              </p>
            </li>
          </ol>
        </section>
      </div>
    </main>
  );
}