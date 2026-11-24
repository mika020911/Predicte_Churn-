---
description: Étape 7 (frontend) : corrections préalables + actions de rétention
agent: build
---
CORRECTIONS PRÉALABLES (frontend) :
1. Aligne le maxLength des mots de passe sur la règle serveur (72 octets) dans register-form, reset-password-form et accept-invitation-form, avec un message clair.
2. Création/renvoi d'invitation : si email_sent est false, affiche « Email non envoyé : copiez le lien ci-dessous » (le lien copiable reste affiché).

ÉTAPE 7 (FRONTEND uniquement) : actions de rétention. Le backend est déjà en place : lis les schémas et endpoints existants (GET /customers/{id} avec suggested_actions, PATCH /customers/{id}, /customers/{id}/actions, /actions, GET /users). Ne modifie pas le backend.

- features/retention : types, api, page /dashboard/actions (liste des actions avec filtres statut / propriétaire / en retard, entrée dans la navigation).
- Dans customer-detail.tsx : sélecteur de statut de rétention, sélecteur de propriétaire (alimenté par GET /users), actions suggérées avec un bouton « Ajouter » en un clic (action préremplie), timeline des actions (créer, passer en cours / fait / annulé, note, échéance).
- Écriture masquée pour un viewer via canWrite (permissions.ts) ; lecture visible pour tous.

Fin d'étape : résumé de 15 lignes max, puis arrête-toi.