---
description: Étape 8 (backend) : corrections préalables + API d'ingestion
agent: build
---
CORRECTIONS PRÉALABLES (backend, avec tests) :
1. PATCH /customers/{id} : owner_user_id doit appartenir à un utilisateur ACTIF de la même organisation avec un rôle admin ou analyst (sinon 400). Tests : utilisateur désactivé, viewer.
2. À la désactivation d'un membre (PATCH /users/{id} is_active=false et DELETE /users/{id}), mets owner_user_id à NULL pour ses clients. Test.

ÉTAPE 8 (BACKEND uniquement) : API d'ingestion. Prérequis : étapes 1 et 2. Ne touche pas au frontend.

Clés API
- Migration (down_revision = add_retention_actions ; vérifie `alembic heads` puis `alembic upgrade head`) : organizations.api_key_hash (String(64), unique, indexé, nullable), api_key_prefix (String(16), nullable), api_key_created_at (DateTime tz, nullable) ; supprime l'ancienne colonne api_key (clés en clair, jamais affichées : elles sont invalidées). L'inscription ne génère plus de clé.
- Génération : `cs_` + secrets.token_urlsafe(32) ; stocke uniquement le SHA-256 + les 8 premiers caractères comme préfixe visible ; la clé complète n'est renvoyée qu'UNE fois (création/rotation), jamais ailleurs.
- deps.py : get_organization_from_api_key via APIKeyHeader(name="X-API-Key", auto_error=False), recherche par empreinte, vérifie organization.is_active ; sinon 401 (message générique, sans dire si la clé existe).
- Endpoints (admin uniquement, nouveau routeur /settings) : GET /settings/api-key (existe ?, préfixe, date de création ; jamais la clé), POST /settings/api-key/rotate (crée ou remplace ; renvoie la nouvelle clé une seule fois ; l'ancienne devient invalide immédiatement).

Ingestion
- POST /ingest/observations (authentification par clé API uniquement, pas de JWT) : corps JSON { observations: [...] } avec les noms internes (customer_id = identifiant externe, snapshot_date, name/email/phone_number optionnels, les 9 features dont contract_type en 0/1, plan optionnel, plan_tier_rank optionnel 0–1). Maximum 5 000 lignes (422 au-delà) + limite de taille du corps configurable (413). Réutilise ingest_dataframe puis la génération de prédictions (via run_in_threadpool) ; lot créé avec source = "api" et uploaded_by_user_id = None.
- Plans : `plan` n'est accepté que s'il est déjà classé dans org.plan_mapping ; sinon la ligne devient une anomalie (ne fait PAS échouer tout le lot : ajoute à ingest_dataframe l'option nécessaire sans changer le comportement de l'import CSV/Excel). plan_tier_rank envoyé directement est accepté.
- Réponse : résumé { batch_id, status, total_rows, imported_rows, error_rows, anomalies (les 50 premières) }. Un renvoi du même contenu est sans danger (doublons signalés en anomalies, pas d'erreur).
- PAS de /ingest/churn-outcomes (étape 9). PAS de webhooks.

Tests : 401 (sans clé, clé invalide, ancienne clé après rotation, organisation inactive) ; la clé d'une organisation n'écrit que dans cette organisation ; GET /settings/api-key ne renvoie jamais la clé ; analyst/viewer → 403 sur /settings/api-key ; plafond 5 000 lignes ; corps trop gros ; doublons ; plan non classé → anomalie sans échec du lot ; plan_tier_rank direct ; lot visible dans l'historique des imports avec source "api" ; prédictions générées.

Après la migration : lance `alembic heads` (une seule tête) puis `alembic upgrade head` sur la base de dev et vérifie qu'une route répond 200.
Fin d'étape : résumé de 15 lignes max, puis arrête-toi.