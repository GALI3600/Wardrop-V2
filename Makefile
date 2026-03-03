.PHONY: setup db backend migrate test lint clean stop web web-install web-build

# ==================== Setup completo ====================

setup: db venv migrate ## Setup completo (DB + venv + migrations)
	@echo "\n✔ Setup completo! Rode 'make backend' para iniciar o servidor."

# ==================== Database ====================

db: ## Sobe o PostgreSQL via Docker
	docker compose up -d db
	@echo "Aguardando PostgreSQL ficar pronto..."
	@until docker compose exec db pg_isready -U wardrop > /dev/null 2>&1; do sleep 1; done
	@echo "✔ PostgreSQL pronto."

# ==================== Python venv ====================

venv: backend/.venv/bin/activate ## Cria venv e instala dependências

backend/.venv/bin/activate: backend/requirements.txt
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install --upgrade pip
	backend/.venv/bin/pip install -r backend/requirements.txt
	@touch backend/.venv/bin/activate

# ==================== Migrations ====================

migrate: venv db ## Gera e aplica migrations do Alembic
	cd backend && .venv/bin/alembic revision --autogenerate -m "auto" 2>/dev/null || true
	cd backend && .venv/bin/alembic upgrade head
	@echo "✔ Migrations aplicadas."

# ==================== Backend ====================

backend: venv db ## Roda o servidor FastAPI (com reload)
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ==================== Testes ====================

test: venv ## Roda os testes unitários
	cd backend && .venv/bin/pip install -r requirements-test.txt -q
	cd backend && .venv/bin/python -m pytest tests/ -v

test-cov: venv ## Roda testes com cobertura
	cd backend && .venv/bin/pip install -r requirements-test.txt pytest-cov -q
	cd backend && .venv/bin/python -m pytest tests/ -v --cov=app --cov-report=term-missing

# ==================== Web (Next.js) ====================

web-install: ## Instala dependências do frontend web
	cd web && npm install

web: ## Roda o frontend Next.js (dev mode)
	cd web && npm run dev

web-build: ## Build de produção do frontend
	cd web && npm run build

# ==================== Utilidades ====================

env: ## Cria .env a partir do .env.example (se não existir)
	@test -f backend/.env || (cp backend/.env.example backend/.env && echo "✔ .env criado. Edite backend/.env com suas chaves." ) || true
	@test -f backend/.env && echo "backend/.env já existe." || true

health: ## Checa se o backend está rodando
	@curl -sf http://localhost:8000/api/health && echo "" || echo "✘ Backend não está rodando. Rode 'make backend'."

stop: ## Para todos os containers Docker
	docker compose down
	@echo "✔ Containers parados."

clean: ## Remove venv, cache e containers
	docker compose down -v
	rm -rf backend/.venv
	rm -rf backend/__pycache__ backend/app/__pycache__
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✔ Limpo."

# ==================== Help ====================

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
