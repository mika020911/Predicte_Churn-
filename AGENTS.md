ORDRE:  Ouvre seulement les fichiers utiles à l'étape (recherche ciblée, ne relis pas tout le dépôt) 

# ChurnSight : règles pour l'agent
Dépôt churn-saas : backend FastAPI/SQLAlchemy/Alembic, frontend Next.js 14, ml XGBoost+SHAP.
Tu implémentes UNE étape à la fois (donnée par la commande /etape-N). Les étapes précédentes sont déjà dans le code.

## Demmarage
liste en 5 lignes max ce que tu vas modifier, puis code.
## Conventions
- Architecture feature-first (frontend/src/features/<feature>/{api,components,types.ts}, pages dans app/dashboard/...). Messages et libellés en français.
- Tests : SQLite en mémoire (conftest.py), pas de SQL spécifique PostgreSQL dans les chemins testés. Isolation par organisation testée pour chaque nouvelle route.
- Migrations Alembic seulement si l'étape l'exige ; down_revision = dernière migration réelle (vérifie) ; pas d'index partiel Postgres.
- Routes FastAPI : routes fixes (/customers/export, /users/invitations, /imports/template) AVANT les routes paramétrées.
- Sécurité : aucun secret ni token dans les logs ; l'API est la source de vérité des permissions.
- Pas de nouvelle dépendance sans demander (autorisée : openpyxl). Pas de refactor hors étape, pas de modification du README.


- Lance les tests UNE seule fois à la fin, pas après chaque fichier.

## Fin d'étape
Résumé de 15 lignes max : fichiers modifiés, migration, tests ajoutés et résultats, écarts avec le prompt, questions. Puis ARRÊTE-TOI. Je fais le commit.