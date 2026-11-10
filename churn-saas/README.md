# ChurnSight

SaaS de **prédiction du churn par IA explicable**. Une entreprise importe ses données clients (CSV) et ChurnSight indique, pour chaque client, son **risque de départ** et les **3 raisons principales** de ce risque.

> Exemple : *« Client C00042 : risque 72 %. Raisons : inactif depuis 25 jours, 2 échecs de paiement sur 90 jours, baisse d'utilisation de 40 % sur les 30 derniers jours. »*

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Structure du dépôt](#structure-du-dépôt)
- [Installation](#installation)
- [Le module ML](#le-module-ml)
- [API](#api)
- [Tests](#tests)
- [État d'avancement](#état-davancement)
- [Limites connues](#limites-connues)

## Fonctionnalités

- Authentification et isolation des données par organisation (multi-tenant).
- Import de CSV avec **mapping des colonnes** et des valeurs de contrat (« mensuel » / « annuel » deviennent 0 / 1), aperçu avant import, rapport d'anomalies ligne par ligne.
- Détection des doublons (même client à la même date).
- Score de risque de départ par client, calculé à chaque import.
- Explication de chaque score par **SHAP** : les 3 facteurs qui augmentent le plus le risque, en français.
- Zones de risque (`low`, `medium`, `high`) selon des **seuils réglables par organisation**.
- Une seule prédiction active par client : celle de son observation la plus récente.

## Architecture

| Couche | Technologie |
|---|---|
| Frontend | Next.js |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Base de données | PostgreSQL 16 (pgAdmin pour l'administration) |
| Machine learning | XGBoost (modèle retenu), Random Forest (comparaison), SHAP |
| Conteneurs | Docker Compose |

Flux d'un import : CSV, puis validation et mapping, puis `observations`, puis le modèle ML (`ml/src/predict.py`), puis `predictions` (score, zone de risque, raisons, valeurs SHAP).

## Structure du dépôt

```
churn-saas/
├── backend/            API FastAPI
│   ├── app/
│   │   ├── api/v1/endpoints/   routes (auth, imports)
│   │   ├── models/             tables SQLAlchemy
│   │   └── services/           import_service, prediction_service, ml_client
│   ├── alembic/                migrations
│   └── tests/
├── frontend/           application Next.js
├── ml/                 module de machine learning
│   ├── src/            code (données, benchmark, SHAP, prédiction)
│   ├── data/raw/       jeu de données synthétique
│   ├── models/         modèles entraînés (voir plus bas)
│   ├── reports/        métriques et graphiques
│   └── tests/
└── docker-compose.yml
```

## Installation

### Prérequis

- Docker et Docker Compose
- Python 3.14 (version utilisée pendant le développement)
- Node.js 20 ou plus

### 1. Variables d'environnement

Crée un fichier `.env` à la racine de `churn-saas/` :

```env
POSTGRES_USER=churnsight
POSTGRES_PASSWORD=change-me
POSTGRES_DB=churnsight
DATABASE_URL=postgresql://churnsight:change-me@localhost:5433/churnsight
SECRET_KEY=une-longue-chaine-aleatoire
```

Le port `5433` de la machine correspond au `5432` du conteneur PostgreSQL. Ne commite jamais ce fichier.

### 2. Base de données

```bash
docker compose up -d db pgadmin
```

pgAdmin est disponible sur http://localhost:5050.

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Documentation interactive (Swagger) : http://localhost:8000/docs

### 4. Modèle ML (obligatoire avant le premier import)

Les fichiers de modèle (`*.pkl`) ne sont **pas** versionnés. Sur un clone neuf, génère-les (environ une minute) :

```bash
cd ml/src
python benchmark.py
python make_metadata.py
```

Sans cette étape, le calcul des prédictions échoue au premier import.

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Application : http://localhost:3000

## Le module ML

### Données

Faute de données clients réelles, le jeu de données est **synthétique** (`ml/src/generate_data.py`, 6 000 clients, 18 % de churn). Un score est calculé à partir de règles connues (ancienneté, type de contrat, inactivité, échecs de paiement, etc.) auxquelles s'ajoutent du bruit et des effets de seuil non linéaires. La difficulté est réglée dans `ml/src/config.py` pour qu'une régression logistique atteigne environ 0,86 d'AUC-ROC.

Les 8 variables d'entrée :

| Variable | Signification |
|---|---|
| `tenure_months` | ancienneté du client, en mois |
| `contract_type` | 0 = mensuel, 1 = annuel |
| `mrr_change_pct` | variation en % du revenu mensuel (négatif = baisse de forfait) |
| `support_tickets_30d` | tickets de support ouverts sur 30 jours |
| `recency_days` | jours depuis la dernière activité |
| `frequency_trend_30d` | évolution de la fréquence d'usage (1,0 = stable, moins de 1 = en baisse) |
| `engagement_breadth` | part des fonctionnalités utilisées (0 à 1) |
| `payment_failures_90d` | échecs de paiement sur 90 jours |

### Méthode

1. **Découpage temporel** sur `snapshot_date` : 70 % entraînement, 15 % validation, 15 % test.
2. **Benchmark** : Random Forest et XGBoost, réglages cherchés par recherche aléatoire (20 essais, validation croisée sur l'entraînement uniquement). La régression logistique sert de référence. Le gagnant est choisi sur l'**AUC-PR** de validation.
3. **Calibration** isotonique évaluée sur le jeu de test (utilisé une seule fois).
4. **SHAP** (`TreeExplainer`) : seules les contributions qui augmentent le risque sont retenues, et chaque facteur est traduit en phrase selon la valeur réelle du client.

### Résultats

Validation (seuil de décision 0,4) :

| Modèle | AUC-PR | AUC-ROC | Brier | Rappel | Précision | F1 |
|---|---|---|---|---|---|---|
| Régression logistique (référence) | 0,616 | 0,842 | 0,110 | 0,49 | 0,60 | 0,54 |
| Random Forest | 0,701 | 0,868 | 0,094 | 0,52 | 0,79 | 0,63 |
| **XGBoost (retenu)** | **0,721** | 0,867 | 0,092 | 0,55 | 0,80 | 0,65 |

Examen final sur le jeu de test :

| | AUC-PR | AUC-ROC | Brier | ECE |
|---|---|---|---|---|
| XGBoost brut (utilisé) | 0,748 | 0,902 | 0,079 | 0,016 |
| Après calibration isotonique | 0,729 | 0,904 | 0,081 | 0,024 |

La calibration n'apporte **aucun gain** : XGBoost est déjà bien calibré (ECE de 0,016). Le modèle brut est donc utilisé en production, et le résultat est documenté dans `ml/reports/calibration_results.json`.

Graphiques : `ml/reports/benchmark_curves.png`, `calibration_curve.png`, `shap_summary.png`.

### Régénérer tout le pipeline

```bash
cd ml/src
python generate_data.py      # données synthétiques
python check_difficult.py    # contrôle de la difficulté (AUC LR entre 0,80 et 0,88)
python benchmark.py          # comparaison RF / XGBoost, sauvegarde du gagnant
python calibrate.py          # calibration + examen final sur le test
python explain.py            # démonstration SHAP et graphique
python make_metadata.py      # carte d'identité du modèle (models/metadata.json)
python predict.py            # test rapide de prédiction
```

### Utilisation depuis Python

```python
from predict import get_predictor

result = get_predictor().predict({
    "tenure_months": 3, "contract_type": 0, "mrr_change_pct": -15.0,
    "support_tickets_30d": 4, "recency_days": 25, "frequency_trend_30d": 0.6,
    "engagement_breadth": 0.3, "payment_failures_90d": 2,
})
# {"score": 0.99, "top_reasons": [...], "shap_values": {...}, "model_version": "..."}
```

`predict()` renvoie le score et les raisons. La **zone de risque** n'est pas calculée par le module ML : le backend la déduit du score et des seuils de l'organisation.

## API

Préfixe : `/api/v1`. Documentation complète sur `/docs`.

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/auth/...` | authentification |
| `GET` | `/imports/template` | télécharger le CSV modèle |
| `POST` | `/imports/preview` | aperçu des colonnes et du mapping, sans écrire en base |
| `PUT` | `/imports/mapping` | enregistrer le mapping de l'organisation |
| `POST` | `/imports/upload` | importer un CSV et calculer les prédictions |
| `GET` | `/imports/` | liste des imports |
| `GET` | `/imports/{id}` | détail et rapport d'anomalies d'un import |

Format minimal d'un CSV d'import :

```csv
customer_id,snapshot_date,tenure_months,contract_type,mrr_change_pct,support_tickets_30d,recency_days,frequency_trend_30d,engagement_breadth,payment_failures_90d
C00001,2026-11-01,36,annuel,2.5,0,2,1.05,0.85,0
C00002,2026-11-01,3,mensuel,-15.0,4,25,0.60,0.30,2
```

Le CSV doit être séparé par des **virgules**. Si tu l'ouvres dans Excel avec une configuration régionale française, ne le réenregistre pas : Excel le réécrirait avec des points-virgules.

## Tests

```bash
# Backend
cd backend && python -m pytest

# Module ML (nécessite d'avoir généré le modèle, voir « Modèle ML »)
cd ml && python -m pytest tests -q
```

Les tests ML vérifient notamment : score entre 0 et 1, au plus 3 raisons toutes positives, erreur claire si une colonne manque, valeurs absentes acceptées, découpage temporel sans chevauchement.

## État d'avancement

- [x] Modèle de données (clients, observations, prédictions, alertes, seuils de risque)
- [x] Import CSV avec mapping, validation et rapport d'anomalies
- [x] Module ML : benchmark, SHAP, prédiction, tests
- [x] Calcul des prédictions à chaque import
- [ ] Création des alertes pour les clients à haut risque
- [ ] Endpoints de consultation des clients et des prédictions
- [ ] Dockerfiles du backend et du frontend (le `docker-compose.yml` les référence déjà)

## Limites connues

- **Données synthétiques.** Les métriques mesurent la capacité du modèle à retrouver les règles du générateur, pas une performance réelle. Les dates étant tirées au hasard, le découpage temporel ne mesure aucune dérive dans le temps.
- Les modèles entraînés ne sont pas versionnés dans Git : il faut les régénérer sur chaque nouvelle machine.
- L'import ne met pas à jour une observation existante : une ligne déjà importée à la même date est rejetée (`DUPLICATE_SNAPSHOT`).
- Avec de vraies données, le modèle devra être réentraîné sur l'historique de chaque organisation.

## Auteur

[@mika020911](https://github.com/mika020911)