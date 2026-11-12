"use client";

import Link from "next/link";
import {usePathname} from "next/navigation";
import {useAuth} from "@/features/auth/context/auth-context";

const links = [
    {href: "/dashboard/customers", label: "Clients"},
    {href: "/dashboard/imports", label: "Importer un CSV"},
    { href: "/dashboard/imports/history", label: "Historique des imports" },
]

export function DashboardNav() {
    const pathname = usePathname();
    const {logout} = useAuth();

  return (
    <nav className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-300 bg-white px-6 py-4">
      <div className="flex flex-wrap gap-3">
        {links.map((link) => {
          const active = pathname === link.href;

          return (
            <Link
              key={link.href}
              href={link.href}
              aria-current={active ? "page" : undefined}
              className={`rounded-md px-4 py-2 font-medium ${
                active
                  ? "bg-blue-700 text-white"
                  : "bg-white text-black hover:bg-blue-50"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      <button
        type="button"
        onClick={logout}
        className="rounded-md border border-slate-400 px-4 py-2 font-medium text-black hover:bg-slate-100"
      >
        Se déconnecter
      </button>
    </nav>
  );
}