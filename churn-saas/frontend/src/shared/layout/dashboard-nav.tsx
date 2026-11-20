"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/context/auth-context";

type NavItem = {
  href: string;
  label: string;
  icon: string;
  adminOnly?: boolean;
};

const navItems: NavItem[] = [
  { href: "/dashboard", label: "Vue d’ensemble", icon: "/icons/maison.png" },
  { href: "/dashboard/customers", label: "Clients", icon: "/icons/client.png" },
  {
    href: "/dashboard/imports",
    label: "Importer des fichiers",
    icon: "/icons/importation-de-fichiers.png",
  },
  {
    href: "/dashboard/imports/history",
    label: "Historique",
    icon: "/icons/historique.png",
  },
  {
    href: "/dashboard/settings",
    label: "Paramètres",
    icon: "/icons/parametres.png",
  },
];

type DashboardNavProps = {
  mobileOpen: boolean;
  onNavigate: () => void;
};

function isActive(href: string, pathname: string) {
  if (href === "/dashboard") return pathname === href;

  if (href === "/dashboard/imports") {
    return (
      pathname === href ||
      (pathname.startsWith(`${href}/`) &&
        !pathname.startsWith(`${href}/history`))
    );
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function DashboardNav({
  mobileOpen,
  onNavigate,
}: DashboardNavProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || user?.role === "admin",
  );

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Fermer le menu"
          onClick={onNavigate}
          className="fixed inset-0 z-40 bg-blue-950/40 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[270px] flex-col border-r border-blue-100 bg-white transition-transform duration-200 lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center gap-3 border-b border-blue-100 px-6">
          <span
            aria-hidden="true"
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-800 font-bold text-white"
          >
            CS
          </span>
          <span className="text-xl font-bold text-black">ChurnSight</span>
        </div>

        <nav aria-label="Navigation principale" className="flex-1 space-y-2 p-4">
          <p className="px-3 pb-2 pt-3 text-xs font-bold uppercase tracking-wider text-blue-900">
            Espace de travail
          </p>

          {visibleItems.map((item) => {
            const active = isActive(item.href, pathname);

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                onClick={onNavigate}
                className={`flex items-center gap-3 rounded-xl px-3 py-3 font-semibold transition ${
                  active
                    ? "bg-blue-100 text-black"
                    : "text-black hover:bg-blue-50"
                }`}
              >
                <img
                  src={item.icon}
                  alt=""
                  aria-hidden="true"
                  className="h-5 w-5 shrink-0 object-contain"
                />
                <span>{item.label}</span>
                {active && (
                  <span
                    aria-hidden="true"
                    className="ml-auto h-2 w-2 rounded-full bg-blue-800"
                  />
                )}
              </Link>
            );
          })}

        </nav>

        <div className="border-t border-blue-100 p-4">
          <p className="px-3 text-xs leading-5 text-black">
            Analyse et compréhension du risque client
          </p>
        </div>
      </aside>
    </>
  );
}