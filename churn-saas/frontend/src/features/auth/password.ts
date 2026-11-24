/**
 * Règle de mot de passe alignée sur le backend (app/core/passwords.py).
 * bcrypt refuse les mots de passe de plus de 72 octets UTF-8.
 */
export const PASSWORD_MIN_LENGTH = 12;
export const PASSWORD_MAX_BYTES = 72;

export function passwordByteLength(value: string): number {
  return new TextEncoder().encode(value).length;
}

/** Message d'erreur à afficher, ou null si le mot de passe respecte la règle. */
export function passwordRuleError(value: string): string | null {
  if (value.length < PASSWORD_MIN_LENGTH) {
    return `Le mot de passe doit contenir au moins ${PASSWORD_MIN_LENGTH} caractères.`;
  }
  if (passwordByteLength(value) > PASSWORD_MAX_BYTES) {
    return "Le mot de passe ne doit pas dépasser 72 octets (un caractère accentué compte pour 2 octets ou plus).";
  }
  return null;
}

export const PASSWORD_MAX_LENGTH = PASSWORD_MAX_BYTES;
export const PASSWORD_HELP =
  "12 caractères minimum, 72 octets maximum (un caractère accentué compte pour 2 octets ou plus).";
