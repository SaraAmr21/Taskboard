.DEFAULT_GOAL := help
SHELL := /bin/bash
COMPOSE := docker compose
PROD := docker compose -f docker-compose.yml -f docker-compose.prod.yml

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- local dev
.PHONY: init
init:
	@test -f .env || (cp .env.example .env && echo "Created .env -- edit the passwords.")

.PHONY: up
up: init
	$(COMPOSE) up -d --build
	@echo "Open http://localhost"

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: destroy
destroy:
	$(COMPOSE) down -v

.PHONY: logs
logs:
	$(COMPOSE) logs -f --tail=100

.PHONY: ps
ps:
	$(COMPOSE) ps

.PHONY: shell
shell:
	$(COMPOSE) exec app /bin/bash

.PHONY: psql
psql:
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-taskboard} -d $${POSTGRES_DB:-taskboard}

.PHONY: monitoring
monitoring:
	$(COMPOSE) --profile monitoring up -d

.PHONY: install
install:
	pip install -r requirements-dev.txt

.PHONY: test
test:
	pytest -v --cov=app --cov-report=term-missing

.PHONY: lint
lint:
	ruff check .
	ruff format --check .

.PHONY: fmt
fmt:
	ruff format .
	ruff check --fix .

.PHONY: security
security:
	bandit -r app -ll
	@command -v trivy >/dev/null && trivy image taskboard:local || \
	  echo "Trivy not installed -- see https://trivy.dev for install instructions"

.PHONY: freeze
freeze:
	pip freeze > requirements.lock

.PHONY: ci
ci: lint test

# ------------------------------------------------------------------ release
.PHONY: build
build:
	docker build --build-arg APP_VERSION=$$(git rev-parse --short HEAD 2>/dev/null || echo dev) -t taskboard:local .

.PHONY: deploy
deploy:
	$(PROD) pull app
	$(PROD) up -d --remove-orphans

.PHONY: backup
backup:
	bash scripts/backup.sh

.PHONY: restore
restore:
	bash scripts/restore.sh $(FILE)

# ---------------------------------------------------------------- terraform
.PHONY: tf-init tf-plan tf-apply tf-destroy
tf-init:
	cd terraform && terraform init
tf-plan:
	cd terraform && terraform fmt && terraform validate && terraform plan
tf-apply:
	cd terraform && terraform apply
tf-destroy:
	cd terraform && terraform destroy
