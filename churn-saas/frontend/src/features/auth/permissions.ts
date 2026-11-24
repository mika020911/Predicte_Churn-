import type { Role } from "./types";

/** Administration de l'organisation (membres, invitations, audit, clés API). */
export function canManageTeam(role?: Role | null): boolean {
  return role === "admin";
}

/** Modification des paramètres d'organisation (seuils de risque, intégrations). */
export function canManageSettings(role?: Role | null): boolean {
  return role === "admin";
}

/** Actions d'écriture métier : import, simulation, rétention, départs. */
export function canWrite(role?: Role | null): boolean {
  return role === "admin" || role === "analyst";
}

/** Import et mapping de fichiers. */
export function canImport(role?: Role | null): boolean {
  return canWrite(role);
}
