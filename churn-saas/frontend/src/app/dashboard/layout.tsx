import type { ReactNode } from "react";
import { DashboardShell } from "@/shared/layout/dashboard-shell";

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <DashboardShell>{children}</DashboardShell>;
}