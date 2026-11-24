---
description: Étape 7 (backend) : corrections préalables + actions de rétention
agent: build
---
CORRECTIONS PRÉALABLES (backend, avec leurs tests) :
1. core/passwords.py : refuse un mot de passe de plus de 72 octets UTF-8 (limite de bcrypt) avec un message clair, à la place du maximum de 128 caractères. Test : 73 caractères → 422 (et non 500) pour register, reset et accept.
2. email_service._send_email : en dry-run, renvoie False (aucun email n'est parti). Adapte les tests.
3. invitation_service.accept_invitation : intercepte IntegrityError (double acceptation du même jeton) et renvoie 409. Test.
4. GET /users : lecture autorisée à admin ET analyst (PATCH, DELETE et invitations restent admin uniquement), car l'étape 7 en a besoin. Test : analyst 200, viewer 403.

ÉTAPE 7 (BACKEND uniquement) : actions de rétention. Prérequis : étapes 1 et 5. Ne touche pas au frontend.

- Migration propre à cette étape : customers.retention_status (none|to_contact|contacted|retained|ignored, défaut none), customers.owner_user_id (FK users, nullable), table customer_actions (id, customer_id, created_by_user_id, action_type call|email|discount|onboarding|other, status todo|in_progress|done|cancelled, note, due_date, completed_at, timestamps). PAS de churned_at ni churn_reason (étape 9).
- services/retention_service.py : playbook sur les 9 features, qui tient compte de la VALEUR de l'observation (ex. mrr_change_pct positif ≠ « revoir le forfait »). recency_days → relance de réactivation ; payment_failures_90d → vérifier le moyen de paiement ; frequency_trend_30d / engagement_breadth → session d'onboarding ; support_tickets_30d → escalade support ; mrr_change_pct (en baisse) → revoir le forfait ; contract_type=0 → proposer l'annuel ; plan_tier_rank bas → montée en gamme ; tenure_months non actionnable. Action par défaut si aucune raison n'est actionnable. 3 suggestions maximum, ordonnées par impact (à partir des top_reasons de la prédiction active). Expose `suggested_actions` dans GET /customers/{id}.
- Endpoints : PATCH /customers/{id} (retention_status, owner_user_id ; l'owner doit être de la même organisation), GET|POST /customers/{id}/actions, PATCH /actions/{id} (annuler = status cancelled, pas de suppression physique), GET /actions?status=&owner=&overdue=. Isolation via Customer.organization_id (customer_actions n'a pas de colonne organisation). Écriture réservée analyst/admin, lecture pour tous les rôles. Règle : retention_status se modifie à la main ; les actions servent de journal.
- Tests : CRUD, transitions de statut, isolation, mapping du playbook (dont mrr positif et action par défaut), filtres, owner d'une autre organisation refusé, viewer 403 en écriture.

Fin d'étape : résumé de 15 lignes max, puis arrête-toi.