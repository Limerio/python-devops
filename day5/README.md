# DevOps Monitoring Dashboard

Système de monitoring temps réel en Python : API FastAPI, dashboard Streamlit, containerisation Docker et pipeline CI GitHub Actions. Tout s'exécute en local — pas de cloud.

## Architecture

- **api** (port 8000) — métriques système, CRUD serveurs, WebSocket live
- **dashboard** (port 8501) — KPIs, graphique live, tableau serveurs coloré

## Prérequis

- Python 3.11 (obligatoire — `make install` utilise `python3.11`)
- Docker et Docker Compose
- Make

## Démarrage rapide

```bash
cd Day5/devops-monitor
cp .env.example .env   # remplir API_KEY
make install
make up
```

- API : http://localhost:8000/docs
- Dashboard : http://localhost:8501

## Commandes Makefile

| Commande | Description |
|----------|-------------|
| `make install` | Installe les dépendances Python |
| `make lint` | Vérifie le code (flake8) |
| `make test` | Tests unitaires (couverture ≥ 75 %) |
| `make build` | Construit les images Docker (sans push) |
| `make integration-test` | Build images, démarre la stack (sans rebuild), tests d'intégration |
| `make up` | Démarre la stack |
| `make down` | Arrête et nettoie la stack |
| `make logs` | Logs des conteneurs |
| `make dev` | Instructions pour le dev sans Docker |

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `API_KEY` | Clé pour `POST /servers`, `DELETE`, `POST /check` |
| `API_BASE_URL` | URL de l'API vue par le dashboard (`http://api:8000` dans Docker) |

## CI GitHub Actions

Pipeline en 3 jobs : `lint` → `test` → `docker`

Workflow : `.github/workflows/devops-monitor-ci.yml` (à la racine du dépôt cours)

Chaque job appelle les cibles `make` correspondantes. Le job `docker` exécute `make integration-test` : build des images, démarrage de la stack avec `--no-build`, puis tests bout-en-bout. Aucun push vers un registry.

## Tests

```bash
make test              # unitaires
make integration-test  # bout-en-bout (nécessite Docker)
```
