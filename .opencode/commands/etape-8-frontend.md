---
description: Étape 8 (frontend) : section Intégrations (clé API)
agent: build
---
ÉTAPE 8 (FRONTEND uniquement) : le backend est déjà en place (GET /settings/api-key, POST /settings/api-key/rotate, POST /ingest/observations). Lis les schémas existants. Ne modifie pas le backend.

- features/settings : api (getApiKeyInfo, rotateApiKey) et components/integrations-panel.tsx, ajouté à la page /dashboard/settings sous les seuils de risque, visible et utilisable seulement avec canManageSettings (permissions.ts) ; les autres rôles ne voient pas la section.
- Affichage : état « aucune clé » ou « clé cs_xxxxxxxx… créée le … » (jamais la clé complète). Bouton « Générer une clé » / « Régénérer » avec confirmation explicite (« l'ancienne clé cessera de fonctionner immédiatement »).
- Après génération : la clé complète s'affiche UNE seule fois dans un encadré avec bouton « Copier » et l'avertissement « Elle ne sera plus visible ». Elle disparaît quand on quitte la page ou recharge (ne la stocke ni en localStorage ni dans l'URL).
- Exemple d'appel (curl) avec une clé factice et un JSON d'exemple (noms internes), bouton « Copier l'exemple ».
- Historique des imports : afficher « API » pour les lots dont source = "api".
Fin d'étape : résumé de 15 lignes max, puis arrête-toi.