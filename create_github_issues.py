#!/usr/bin/env python3
"""
Crée les labels, les milestones (sprints) et les issues GitHub de ChurnSight
à partir de la planification du cahier des charges (section 4.4.2).

Prérequis :
  1. Installer GitHub CLI : https://cli.github.com
  2. Se connecter : gh auth login
  3. Créer le dépôt sur GitHub (vide ou non)

Utilisation :
  python create_github_issues.py --repo mika020911/churn-saas --dry-run   # simulation
  python create_github_issues.py --repo mika020911/churn-saas             # création réelle

Ne le lance qu'UNE fois en mode réel, sinon les issues seront dupliquées.
"""
import argparse
import subprocess
import sys

# ---------------------------------------------------------------- Labels
LABELS = {
    "ml": ("7057ff", "Machine learning"),
    "backend": ("0e8a16", "API FastAPI / services"),
    "frontend": ("1d76db", "Next.js / interface"),
    "database": ("fbca04", "PostgreSQL / schéma"),
    "auth": ("b60205", "Authentification et rôles"),
    "tests": ("5319e7", "Tests unitaires / E2E"),
    "docs": ("c5def5", "Documentation / rapport"),
    "bug": ("d73a4a", "Correction d'anomalies"),
    "priorité-haute": ("d93f0b", "Priorité haute"),
    "priorité-moyenne": ("fbca04", "Priorité moyenne"),
    "priorité-basse": ("0e8a16", "Priorité basse"),
    "1j": ("ededed", "Estimation : 1 jour"),
    "2j": ("ededed", "Estimation : 2 jours"),
}

# ------------------------------------------------------------ Milestones
MILESTONES = {
    1: "Sprint 1 - Données, auth, import CSV (US01, US06)",
    2: "Sprint 2 - Prédiction du score de risque (US02)",
    3: "Sprint 3 - Explicabilité SHAP (US03)",
    4: "Sprint 4 - Dashboard et alertes (US04, US05)",
    5: "Sprint 5 - Rôles et finalisation (US07)",
}

# ---------------------------------------------------------------- Issues
# (sprint, user story, titre, jours, labels, description, critères d'acceptation)
TASKS = [
    # ---------------- Sprint 1
    (1, "US01", "Générer un jeu de données synthétique réaliste", 2,
     ["ml", "priorité-haute"],
     "Générer un CSV d'au moins 5000 lignes avec les 10 variables du dictionnaire de données "
     "(tenure_months, contract_type, engagement_breadth, frequency_trend_30d, mrr_change_pct, "
     "payment_failures_90d, recency_days, support_tickets_30d, snapshot_date, churn).\n\n"
     "Points clés : distributions réalistes, corrélations entre variables, churn tiré par "
     "probabilité (sigmoïde + Bernoulli), bruit, snapshot_date étalée sur ~12 mois, "
     "aucune fuite de données.",
     ["Fichier `ml/data/churn_data.csv` généré avec une graine fixe (seed=42)",
      "≥ 5000 lignes, taux de churn entre 8 % et 15 %",
      "Corrélations plausibles (matrice de corrélation vérifiée)",
      "Une régression logistique donne une AUC correcte mais pas parfaite (~0.80-0.88)",
      "Aucune variable calculée à partir de la cible (pas de data leakage)"]),

    (1, "US01", "Créer le schéma PostgreSQL (Users, Customers)", 1,
     ["database", "backend", "priorité-haute"],
     "Créer les tables Users et Customers avec clés primaires, clés étrangères et contraintes "
     "d'intégrité. Prévoir les migrations (Alembic).",
     ["Tables Users et Customers créées via migration",
      "Contraintes d'unicité (email) et d'intégrité référentielle en place",
      "Connexion SQLAlchemy opérationnelle dans `database.py`",
      "Base lancée via Docker Compose"]),

    (1, "US06", "Développer l'authentification JWT", 1,
     ["auth", "backend", "priorité-haute"],
     "Inscription et connexion par email + mot de passe, hachage du mot de passe, "
     "émission et vérification de tokens JWT, dépendance de protection des routes.",
     ["Endpoints `/auth/register` et `/auth/login`",
      "Mot de passe haché (bcrypt/argon2), jamais stocké en clair",
      "Routes protégées renvoyant 401 sans token valide",
      "Expiration du token configurée via variable d'environnement"]),

    (1, "US01", "Créer l'endpoint d'import CSV avec validation", 1,
     ["backend", "priorité-haute"],
     "Endpoint d'upload d'un CSV de clients avec validation du schéma (colonnes, types, "
     "plages de valeurs) et insertion en base. Rejet clair en cas de fichier invalide.",
     ["Endpoint `POST /customers/import` protégé par JWT",
      "Colonnes manquantes ou types invalides : erreur 422 avec message explicite",
      "Lignes valides insérées en base",
      "Résumé d'import renvoyé (lignes importées / rejetées)"]),

    (1, "US01 / US06", "Écrire les tests unitaires de l'import et de l'authentification", 1,
     ["tests", "backend", "priorité-haute"],
     "Tests Pytest couvrant l'authentification et l'import CSV (cas nominaux et cas d'erreur).",
     ["Tests d'inscription, de connexion et d'accès refusé",
      "Tests d'import : CSV valide, colonne manquante, type invalide",
      "Tous les tests passent avec `pytest`"]),

    # ---------------- Sprint 2
    (2, "US02", "Intégrer le modèle Random Forest sérialisé dans ml_service", 1,
     ["ml", "backend", "priorité-haute"],
     "Entraîner le Random Forest (class_weight='balanced'), le sérialiser avec joblib et le "
     "charger au démarrage de l'API dans un service dédié `ml_service`.",
     ["Modèle sauvegardé dans `ml/models/random_forest_churn.pkl`",
      "`ml_service` charge le modèle une seule fois au démarrage",
      "Fonction `predict_proba(customer)` testée sur un exemple"]),

    (2, "US02", "Développer l'endpoint de prédiction /predict", 1,
     ["backend", "priorité-haute"],
     "Endpoint qui reçoit un ou plusieurs clients, appelle `ml_service` et renvoie la "
     "probabilité de churn à 30 jours.",
     ["Endpoint `POST /predict` protégé par JWT",
      "Validation des entrées avec Pydantic",
      "Réponse : probabilité entre 0 et 1 par client",
      "Documentation Swagger à jour"]),

    (2, "US02", "Enregistrer les prédictions et archiver la précédente", 1,
     ["backend", "database", "priorité-haute"],
     "Table Predictions avec une seule prédiction active par client. Toute nouvelle "
     "prédiction archive la précédente (règle de gestion).",
     ["Table Predictions créée par migration",
      "Une seule prédiction active par client à tout moment",
      "L'ancienne prédiction passe en archive, l'historique est conservé",
      "Test de la règle de gestion"]),

    (2, "US02", "Calibrer les probabilités et définir les seuils vert / orange / rouge", 1,
     ["ml", "priorité-haute"],
     "Appliquer la calibration isotonique après l'entraînement, puis définir les seuils "
     "de zones de risque. Produire la courbe de calibration.",
     ["Calibration isotonique appliquée (CalibratedClassifierCV)",
      "Courbe de calibration générée dans `ml/reports/`",
      "Seuils vert / orange / rouge configurables",
      "Zone de risque renvoyée par l'API avec le score"]),

    (2, "US02", "Développer la page liste des clients avec score de risque", 2,
     ["frontend", "priorité-haute"],
     "Page Next.js listant les clients avec leur score, leur zone colorée, avec tri et "
     "filtre par zone de risque.",
     ["Tableau paginé des clients avec score en pourcentage",
      "Badge de couleur vert / orange / rouge",
      "Tri par score et filtre par zone",
      "États de chargement et d'erreur gérés"]),

    (2, "US02", "Écrire les tests unitaires du service de prédiction", 1,
     ["tests", "ml", "priorité-haute"],
     "Tests Pytest du service de prédiction et de l'archivage des prédictions.",
     ["Test de la probabilité renvoyée (bornes 0 à 1)",
      "Test de l'archivage de la prédiction précédente",
      "Test des seuils de zones",
      "Tous les tests passent"]),

    # ---------------- Sprint 3
    (3, "US03", "Intégrer SHAP TreeExplainer et extraire les 3 facteurs principaux", 1,
     ["ml", "priorité-haute"],
     "Calculer les valeurs SHAP avec TreeExplainer et extraire, pour chaque client, les "
     "3 variables les plus contributives au risque.",
     ["TreeExplainer chargé dans `ml_service`",
      "Fonction renvoyant les 3 facteurs principaux (variable, valeur, contribution)",
      "Temps de calcul acceptable pour un client"]),

    (3, "US03", "Créer le dictionnaire de gabarits de phrases d'explication", 1,
     ["ml", "priorité-haute"],
     "Traduire chaque variable et son sens de contribution en phrase lisible, par exemple "
     "« Baisse d'utilisation de X % sur les 30 derniers jours ».",
     ["Un gabarit par variable et par sens (hausse / baisse du risque)",
      "Phrases générées avec la vraie valeur du client",
      "Aucune phrase technique (pas de « SHAP » ni de nom de colonne brut)"]),

    (3, "US03", "Exposer les explications dans l'API", 1,
     ["backend", "priorité-haute"],
     "Ajouter les 3 raisons traduites à la réponse de prédiction et à l'endpoint de détail "
     "d'un client.",
     ["Endpoint `GET /customers/{id}` renvoie score, zone et 3 raisons",
      "Schémas Pydantic mis à jour",
      "Explications stockées ou recalculées de façon cohérente"]),

    (3, "US03", "Développer la fiche client détaillée", 2,
     ["frontend", "priorité-haute"],
     "Page de détail d'un client : score, zone de risque, 3 raisons SHAP, variables clés "
     "et historique des prédictions.",
     ["Route `/customers/[id]` fonctionnelle",
      "Affichage du score, de la zone et des 3 raisons en langage clair",
      "Historique des prédictions visible",
      "Responsive"]),

    (3, "US03", "Vérifier la cohérence locale et la stabilité des explications", 1,
     ["ml", "tests", "priorité-haute"],
     "Valider l'explicabilité : cohérence locale, stabilité face à une légère perturbation "
     "des entrées, cohérence globale avec le Summary Plot.",
     ["Les 3 raisons affichées correspondent aux variables les plus contributives",
      "Une légère perturbation ne change pas radicalement l'explication",
      "SHAP Summary Plot cohérent avec l'importance globale des variables",
      "Résultats consignés pour le rapport d'évaluation"]),

    # ---------------- Sprint 4
    (4, "US04", "Développer les endpoints d'indicateurs et de segmentation", 1,
     ["backend", "priorité-haute"],
     "Endpoints fournissant les KPIs (nombre de clients, taux de risque moyen, MRR à "
     "risque) et la répartition vert / orange / rouge.",
     ["Endpoint `GET /dashboard/kpis`",
      "Endpoint `GET /dashboard/segmentation`",
      "Requêtes SQL optimisées (agrégations côté base)"]),

    (4, "US04", "Développer le dashboard global", 2,
     ["frontend", "priorité-haute"],
     "Page dashboard avec cartes de KPIs et graphique de segmentation du portefeuille.",
     ["Cartes de KPIs",
      "Graphique de répartition vert / orange / rouge",
      "Liens vers la liste des clients filtrée par zone",
      "États de chargement et d'erreur gérés"]),

    (4, "US05", "Développer alert_service avec la règle d'alerte unique", 1,
     ["backend", "database", "priorité-moyenne"],
     "Service qui déclenche une alerte quand un client passe en zone rouge, une seule fois "
     "par passage, sans doublon tant qu'il reste en zone rouge.",
     ["Table Alerts rattachée à une prédiction en zone rouge",
      "Pas de doublon tant que le client reste en zone rouge",
      "Nouvelle alerte possible après un retour hors zone rouge puis un nouveau passage"]),

    (4, "US05", "Mettre en place les alertes in-app", 1,
     ["backend", "frontend", "priorité-moyenne"],
     "Afficher les alertes dans l'application (cloche de notifications, liste, statut lu "
     "ou non lu).",
     ["Compteur d'alertes non lues",
      "Liste des alertes avec lien vers la fiche client",
      "Marquage « lu »"]),

    (4, "US05", "Mettre en place les alertes par email", 1,
     ["backend", "priorité-moyenne"],
     "Envoi d'un email à l'analyste lors d'une nouvelle alerte (SMTP configurable via "
     "variables d'environnement, mode simulé en développement).",
     ["Envoi SMTP configurable (`.env`)",
      "Mode développement : email loggé au lieu d'être envoyé",
      "Email contenant le client, le score et les 3 raisons"]),

    (4, "US05", "Écrire les tests unitaires des alertes", 1,
     ["tests", "backend", "priorité-moyenne"],
     "Tests Pytest de la règle d'alerte unique et des canaux in-app et email.",
     ["Test : pas de doublon d'alerte en zone rouge",
      "Test : nouvelle alerte après sortie puis retour en zone rouge",
      "Test de l'envoi d'email (mock SMTP)",
      "Tous les tests passent"]),

    # ---------------- Sprint 5
    (5, "US07", "Développer la gestion des rôles utilisateurs", 2,
     ["auth", "backend", "frontend", "priorité-basse"],
     "Rôle administrateur et rôle analyste. Seul un administrateur peut modifier les seuils "
     "de risque (règle de gestion).",
     ["Champ rôle dans Users, vérifié côté API",
      "Modification des seuils réservée à l'administrateur (403 sinon)",
      "Interface masquant les actions non autorisées"]),

    (5, "Finalisation", "Réaliser les tests de bout en bout", 2,
     ["tests", "priorité-haute"],
     "Tests du parcours complet : connexion, import CSV, prédiction, fiche client, "
     "dashboard, alerte.",
     ["Parcours principal automatisé (Playwright, Cypress ou Jest)",
      "Environnement lancé via Docker Compose",
      "Rapport de tests produit"]),

    (5, "Finalisation", "Corriger les anomalies", 2,
     ["bug", "priorité-haute"],
     "Corriger les anomalies identifiées pendant les tests de bout en bout et la recette.",
     ["Liste des anomalies tracée dans des issues liées",
      "Anomalies bloquantes et majeures corrigées",
      "Non-régression vérifiée"]),

    (5, "Finalisation", "Rédiger la documentation et le rapport d'évaluation ML", 1,
     ["docs", "ml", "priorité-haute"],
     "README (installation, lancement, variables d'environnement) et rapport d'évaluation "
     "du modèle.",
     ["README complet avec instructions Docker Compose",
      "Rapport ML : AUC-ROC, recall, AUC-PR, precision, F1",
      "Matrice de confusion, courbes ROC, Precision-Recall et calibration",
      "Évaluation de l'explicabilité SHAP"]),
]


def run(cmd, dry_run, input_text=None):
    """Exécute une commande gh (ou l'affiche en mode simulation)."""
    if dry_run:
        print("  [dry-run]", " ".join(cmd[:6]), "...")
        return True
    result = subprocess.run(
        cmd, input=input_text, text=True, encoding="utf-8",
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"  ! {result.stderr.strip()}")
        return False
    return True


def build_body(us, days, description, criteria):
    checklist = "\n".join(f"- [ ] {c}" for c in criteria)
    return (
        f"**User story :** {us}  \n"
        f"**Estimation :** {days} jour{'s' if days > 1 else ''}\n\n"
        f"## Description\n{description}\n\n"
        f"## Critères d'acceptation\n{checklist}\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="ex. mika020911/churn-saas")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Vérifie que gh est installé
    if not args.dry_run:
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            sys.exit("GitHub CLI (gh) introuvable. Installe-le puis lance `gh auth login`.")

    print("== Labels ==")
    for name, (color, desc) in LABELS.items():
        print(f"- {name}")
        run(["gh", "label", "create", name, "--color", color,
             "--description", desc, "--repo", args.repo, "--force"], args.dry_run)

    print("\n== Milestones (sprints) ==")
    for title in MILESTONES.values():
        print(f"- {title}")
        run(["gh", "api", f"repos/{args.repo}/milestones",
             "-f", f"title={title}", "-f", "state=open"], args.dry_run)

    print("\n== Issues ==")
    total_days = 0
    for sprint, us, title, days, labels, desc, criteria in TASKS:
        full_title = f"[S{sprint}] {title}"
        all_labels = labels + [f"{days}j"]
        print(f"- {full_title} ({days} j)")
        total_days += days
        run(["gh", "issue", "create", "--repo", args.repo,
             "--title", full_title,
             "--label", ",".join(all_labels),
             "--milestone", MILESTONES[sprint],
             "--body-file", "-"],
            args.dry_run, input_text=build_body(us, days, desc, criteria))

    print(f"\nTerminé : {len(TASKS)} issues, {total_days} jours estimés au total.")


if __name__ == "__main__":
    main()
