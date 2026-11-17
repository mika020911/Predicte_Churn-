"use client";

import { useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/context/auth-context";
import { DashboardNav } from "./dashboard-nav";

const pageTitles: Array<{ prefix: string; title: string }> = [
  { prefix: "/dashboard/customers", title: "Clients" },
  { prefix: "/dashboard/imports/history", title: "Historique des imports" },
  { prefix: "/dashboard/imports", title: "Import de fichiers" },
  { prefix: "/dashboard", title: "Vue d’ensemble" },
];

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const pageTitle =
    pageTitles.find(
      (item) =>
        pathname === item.prefix || pathname.startsWith(`${item.prefix}/`),
    )?.title ?? "ChurnSight";

  const initials =
    user?.full_name
      ?.trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "U";

  return (
    <div className="min-h-screen bg-[#f5f8ff] text-black">
      <DashboardNav
        mobileOpen={mobileOpen}
        onNavigate={() => setMobileOpen(false)}
      />

      <div className="min-h-screen lg:pl-[270px]">
        <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-blue-100 bg-white px-4 sm:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label={mobileOpen ? "Fermer le menu" : "Ouvrir le menu"}
              aria-expanded={mobileOpen}
              onClick={() => setMobileOpen((open) => !open)}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-blue-200 text-black lg:hidden"
            >
              {mobileOpen ? (
                <span aria-hidden="true" className="text-2xl leading-none">
                  ×
                </span>
              ) : (
                <span aria-hidden="true" className="text-xl leading-none">
                  ☰
                </span>
              )}
            </button>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-blue-900">
                ChurnSight
              </p>
              <h1 className="text-lg font-bold text-black sm:text-xl">
                {pageTitle}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="max-w-48 truncate text-sm font-semibold text-black">
                {user?.full_name ?? "Mon compte"}
              </p>
              <p className="max-w-48 truncate text-xs text-black">
                {user?.email ?? ""}
              </p>
            </div>

            <span
              aria-label={`Compte ${user?.full_name ?? ""}`}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 font-bold text-violet-950"
            >
              {initials}
            </span>

            <button
              type="button"
              onClick={logout}
              title="Se déconnecter"
              className="flex h-10 items-center gap-2 rounded-xl border border-blue-200 px-3 text-sm font-semibold text-black transition hover:bg-blue-50"
            >
              <img
                src="/icons/logout.png"
                alt=""
                aria-hidden="true"
                className="h-5 w-5 object-contain"
              />
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-[1500px] p-4 sm:p-8">{children}</main>
      </div>
    </div>
  );
}