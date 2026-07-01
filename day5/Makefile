VENV ?= .venv
PYTHON311 ?= python3.11
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
export PYTHONPATH := $(CURDIR)

API_IMAGE = devops-monitor-api
DASHBOARD_IMAGE = devops-monitor-dashboard

.PHONY: install lint test build integration-test up down logs dev

install:
	@command -v $(PYTHON311) >/dev/null 2>&1 || { \
		echo "Erreur: Python 3.11 requis. Installez-le ou définissez PYTHON311=chemin/vers/python3.11"; \
		exit 1; \
	}
	@test -d $(VENV) || $(PYTHON311) -m venv $(VENV)
	$(PIP) install -r requirements.txt

lint:
	$(VENV)/bin/flake8 api/ dashboard/ tests/

test:
	$(VENV)/bin/pytest tests/ -v --ignore=tests/test_integration.py --cov=api --cov-fail-under=75

build:
	docker build -t $(API_IMAGE) -f api/Dockerfile .
	docker build -t $(DASHBOARD_IMAGE) -f dashboard/Dockerfile .

integration-test: build
	@test -f .env || cp .env.example .env
	@grep -qE '^API_KEY=.+$$' .env || echo 'API_KEY=dev-key-change-me' >> .env
	docker compose up -d --wait --no-build
	API_BASE_URL=http://localhost:8000 \
	DASHBOARD_URL=http://localhost:8501 \
	API_KEY=$$(grep '^API_KEY=' .env | cut -d= -f2-) \
		$(VENV)/bin/pytest tests/test_integration.py -v
	docker compose down -v

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

dev:
	@echo "Lancer dans deux terminaux :"
	@echo "  API_KEY=dev-key-change-me uvicorn api.main:app --reload --port 8000"
	@echo "  API_BASE_URL=http://localhost:8000 API_KEY=dev-key-change-me streamlit run dashboard/app.py"
