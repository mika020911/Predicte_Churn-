import Link from "next/link";

const features = [
  {
    number: "01",
    title: "Repérer les clients à risque",
    description:
      "Consultez les scores de risque pour repérer les clients qui pourraient bientôt partir.",
  },
  {
    number: "02",
    title: "Comprendre chaque prédiction",
    description:
      "Découvrez les principaux facteurs associés au risque de départ de chaque client.",
  },
  {
    number: "03",
    title: "Importer vos données simplement",
    description:
      "Importez un fichier CSV, associez ses colonnes et consultez le rapport d’import.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden bg-white text-black">
      {/* Navigation */}
      <header className="relative z-20 border-b border-blue-100 bg-white">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <Link
            href="/"
            aria-label="ChurnSight, accueil"
            className="flex items-center gap-3"
          >
            <img
              src="/images/CHurnSight.gif"
              alt="Logo animé ChurnSight"
              className="h-12 w-12 rounded-xl object-contain"
            />
            <span className="text-xl font-bold tracking-tight text-black">
              ChurnSight
            </span>
          </Link>

          <div className="flex items-center gap-3 sm:gap-5">
            <Link
              href="/auth/login"
              className="hidden font-semibold text-black hover:text-blue-800 sm:inline"
            >
              Se connecter
            </Link>

            <Link
              href="/auth/register"
              className="rounded-full bg-blue-700 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-800"
            >
              Créer un compte
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative isolate">
        <div
          aria-hidden="true"
          className="absolute -right-32 -top-20 -z-10 h-96 w-96 rounded-full bg-blue-100/70 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="absolute -left-40 top-72 -z-10 h-96 w-96 rounded-full bg-violet-100/70 blur-3xl"
        />

        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-2 lg:gap-16">
          <div>
            <p className="mb-6 inline-flex rounded-full border border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-800">
              L’intelligence client au service de la fidélisation
            </p>

            <h1 className="max-w-2xl text-4xl font-bold leading-tight tracking-tight text-black sm:text-5xl lg:text-6xl">
              Comprenez le risque.
              <br />
              <span className="text-blue-800">Agissez plus tôt.</span>
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-8 text-black">
              ChurnSight aide votre équipe à repérer les clients à risque,
              comprendre les facteurs importants et prioriser les actions de
              fidélisation.
            </p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center rounded-full bg-blue-700 px-7 py-3.5 font-semibold text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-800"
              >
                Commencer gratuitement
                <span aria-hidden="true" className="ml-2">
                  →
                </span>
              </Link>

              <Link
                href="/auth/login"
                className="inline-flex items-center justify-center rounded-full border border-blue-300 bg-white px-7 py-3.5 font-semibold text-black transition hover:bg-blue-50"
              >
                Se connecter
              </Link>
            </div>

            <p className="mt-4 text-sm text-black">
              Import CSV · Scores de risque · Explications compréhensibles
            </p>
          </div>

          {/* Visuel fourni par l’utilisatrice */}
          <div className="relative mx-auto w-full max-w-xl">
            <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-blue-200 via-violet-100 to-white blur-xl" />

            <div className="relative overflow-hidden rounded-[2rem] border border-blue-100 bg-white p-3 shadow-2xl">
              <img
                src="/images/login_image.png"
                alt="Illustration de l’analyse ChurnSight"
                className="aspect-[4/3] w-full rounded-[1.5rem] object-cover"
              />

              <div className="absolute bottom-7 left-7 right-7 rounded-2xl border border-white/70 bg-white/95 p-4 shadow-xl backdrop-blur sm:bottom-9 sm:left-9 sm:right-9">
                <p className="text-sm font-semibold text-black">
                  Exemple d’analyse client
                </p>
                <div className="mt-3 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-bold text-black">Risque de départ</p>
                    <p className="mt-1 text-sm text-black">
                      Score explicable et facteurs associés
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-orange-100 px-3 py-1.5 text-sm font-bold text-orange-900">
                    À surveiller
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Fonctionnalités */}
      <section className="border-y border-blue-100 bg-blue-50/50">
        <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20">
          <div className="max-w-2xl">
            <p className="font-semibold text-blue-800">Une approche claire</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-black sm:text-4xl">
              De vos données à une meilleure compréhension client
            </h2>
            <p className="mt-4 leading-7 text-black">
              Rassemblez les informations utiles, observez les niveaux de
              risque et comprenez les raisons affichées par le modèle.
            </p>
          </div>

          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {features.map((feature) => (
              <article
                key={feature.number}
                className="rounded-3xl border border-blue-100 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-700 font-bold text-white">
                  {feature.number}
                </span>
                <h3 className="mt-6 text-xl font-bold text-black">
                  {feature.title}
                </h3>
                <p className="mt-3 leading-7 text-black">
                  {feature.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Appel à l’action */}
      <section className="px-5 py-16 sm:px-8 sm:py-24">
        <div className="mx-auto max-w-5xl rounded-[2rem] bg-blue-800 px-6 py-12 text-center text-white sm:px-12 sm:py-16">
          <h2 className="text-3xl font-bold sm:text-4xl">
            Prêt à mieux comprendre vos clients ?
          </h2>
          <p className="mx-auto mt-4 max-w-2xl leading-7 text-white">
            Créez votre espace ChurnSight et commencez par importer vos données
            clients.
          </p>
          <Link
            href="/auth/register"
            className="mt-8 inline-flex rounded-full bg-white px-7 py-3.5 font-semibold text-blue-900 transition hover:bg-blue-50"
          >
            Créer mon espace
          </Link>
        </div>
      </section>

      {/* Pied de page */}
      <footer className="border-t border-blue-100 px-5 py-7 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-3">
            <img
              src="/images/CHurnSight.gif"
              alt=""
              aria-hidden="true"
              className="h-9 w-9 object-contain"
            />
            <span className="font-semibold text-black">ChurnSight</span>
          </div>

          <p className="text-sm text-black">
            Prédiction et compréhension du risque client.
          </p>

          <Link
            href="/auth/login"
            className="text-sm font-semibold text-blue-800 underline underline-offset-4"
          >
            Se connecter
          </Link>
        </div>
      </footer>
    </main>
  );
}