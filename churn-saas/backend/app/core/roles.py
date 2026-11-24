"""Rôles applicatifs et ensembles de rôles autorisés.

Les rôles sont stockés dans `users.role` (chaîne libre en base). Toute
vérification de permission doit passer par les dépendances de `app.api.deps`
afin de rester fail-closed sur une valeur inconnue.
"""

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"

VALID_ROLES = {ROLE_ADMIN, ROLE_ANALYST, ROLE_VIEWER}
WRITE_ROLES = {ROLE_ADMIN, ROLE_ANALYST}
