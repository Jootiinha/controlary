.PHONY: help install install-dev install-all backend-install backend-install-dev \
	backend-dev backend-test backend-test-cov backend-lint backend-format backend-typecheck \
	frontend-install frontend-dev frontend-build frontend-lint \
	docker-build docker-up docker-down docker-logs docker-logs-backend docker-logs-frontend \
	clean clean-backend clean-frontend cleanup

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Controle Financeiro - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install          Install both backend and frontend"
	@echo "  make install-dev      Install both with dev dependencies"
	@echo "  make install-all      Install all dependencies (same as install-dev)"
	@echo ""
	@echo "$(GREEN)Backend (Python/FastAPI):$(NC)"
	@echo "  make backend-install  Install backend dependencies with Poetry"
	@echo "  make backend-install-dev  Install backend with dev dependencies"
	@echo "  make backend-dev      Start FastAPI development server (with reload)"
	@echo "  make backend-test     Run backend tests"
	@echo "  make backend-test-cov Run backend tests with coverage report"
	@echo "  make backend-lint     Lint backend code with ruff"
	@echo "  make backend-format   Format backend code with black"
	@echo "  make backend-typecheck  Type check backend code with mypy"
	@echo ""
	@echo "$(GREEN)Frontend (Node/Vue):$(NC)"
	@echo "  make frontend-install Install frontend dependencies"
	@echo "  make frontend-dev     Start Vite dev server"
	@echo "  make frontend-build   Build frontend for production"
	@echo "  make frontend-lint    Lint frontend code"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-up        Start containers"
	@echo "  make docker-down      Stop containers"
	@echo "  make docker-logs      Show all logs"
	@echo "  make docker-logs-backend   Show backend logs"
	@echo "  make docker-logs-frontend  Show frontend logs"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-backend    Remove backend build files"
	@echo "  make clean-frontend   Remove frontend build files"
	@echo "  make cleanup          Full cleanup (includes node_modules, venv)"

# ============================================================================
# SETUP
# ============================================================================

install: backend-install frontend-install ## Install dependencies for both backend and frontend
	@echo "$(GREEN)✓ Installation complete!$(NC)"

install-dev: backend-install-dev frontend-install ## Install dependencies including dev dependencies
	@echo "$(GREEN)✓ Installation complete with dev dependencies!$(NC)"

install-all: install-dev ## Alias for install-dev

# ============================================================================
# BACKEND (Python/FastAPI)
# ============================================================================

backend-install: ## Install backend dependencies with Poetry
	@echo "$(CYAN)Installing backend dependencies...$(NC)"
	cd backend && poetry install --only=main
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

backend-install-dev: ## Install backend with dev dependencies
	@echo "$(CYAN)Installing backend with dev dependencies...$(NC)"
	cd backend && poetry install
	@echo "$(GREEN)✓ Backend installed with dev dependencies$(NC)"

backend-dev: ## Start FastAPI development server (with hot reload)
	@echo "$(CYAN)Starting FastAPI development server...$(NC)"
	@echo "$(GREEN)→ http://localhost:8000$(NC)"
	@echo "$(GREEN)→ API Docs: http://localhost:8000/docs$(NC)"
	cd backend && poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

backend-test: ## Run backend tests
	@echo "$(CYAN)Running backend tests...$(NC)"
	cd backend && poetry run pytest

backend-test-cov: ## Run backend tests with coverage report
	@echo "$(CYAN)Running backend tests with coverage...$(NC)"
	cd backend && poetry run pytest --cov=app tests/ --cov-report=html --cov-report=term

backend-lint: ## Lint backend code
	@echo "$(CYAN)Linting backend code...$(NC)"
	cd backend && poetry run ruff check app/

backend-format: ## Format backend code
	@echo "$(CYAN)Formatting backend code...$(NC)"
	cd backend && poetry run black app/

backend-typecheck: ## Type check backend code
	@echo "$(CYAN)Type checking backend code...$(NC)"
	cd backend && poetry run mypy app/

backend-all-checks: backend-lint backend-typecheck backend-test ## Run all backend checks

# ============================================================================
# FRONTEND (Node/Vue)
# ============================================================================

frontend-install: ## Install frontend dependencies
	@echo "$(CYAN)Installing frontend dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

frontend-dev: ## Start Vite development server
	@echo "$(CYAN)Starting Vite dev server...$(NC)"
	@echo "$(GREEN)→ http://localhost:5173$(NC)"
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	@echo "$(CYAN)Building frontend for production...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built to: frontend/dist$(NC)"

frontend-lint: ## Lint frontend code
	@echo "$(CYAN)Linting frontend code...$(NC)"
	cd frontend && npm run lint 2>/dev/null || echo "$(RED)ESLint not configured$(NC)"

# ============================================================================
# DOCKER
# ============================================================================

docker-build: ## Build Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(CYAN)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers running$(NC)"
	@echo "$(GREEN)→ Frontend: http://localhost$(NC)"
	@echo "$(GREEN)→ Backend API: http://localhost:8000$(NC)"
	@echo "$(GREEN)→ API Docs: http://localhost:8000/docs$(NC)"

docker-down: ## Stop Docker containers
	@echo "$(CYAN)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-logs: ## Show all container logs
	docker-compose logs -f

docker-logs-backend: ## Show backend container logs
	docker-compose logs -f backend

docker-logs-frontend: ## Show frontend container logs
	docker-compose logs -f frontend

docker-restart: docker-down docker-up ## Restart all containers

docker-shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

docker-shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

# ============================================================================
# CLEANUP
# ============================================================================

clean-backend: ## Remove backend build artifacts
	@echo "$(CYAN)Cleaning backend...$(NC)"
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -name .coverage -delete 2>/dev/null || true
	cd backend && find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Backend cleaned$(NC)"

clean-frontend: ## Remove frontend build artifacts
	@echo "$(CYAN)Cleaning frontend...$(NC)"
	cd frontend && rm -rf dist/ node_modules/.vite 2>/dev/null || true
	cd frontend && rm -rf .parcel-cache 2>/dev/null || true
	@echo "$(GREEN)✓ Frontend cleaned$(NC)"

clean: clean-backend clean-frontend ## Remove all build artifacts (keep dependencies)
	@echo "$(GREEN)✓ Project cleaned$(NC)"

cleanup: ## Full cleanup including dependencies
	@echo "$(CYAN)Full cleanup (this will remove dependencies)...$(NC)"
	cd backend && rm -rf .venv poetry.lock dist/ build/ *.egg-info 2>/dev/null || true
	cd frontend && rm -rf node_modules/ dist/ build/ 2>/dev/null || true
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd frontend && find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

# ============================================================================
# DEVELOPMENT WORKFLOWS
# ============================================================================

dev: ## Start both backend and frontend dev servers (requires 2 terminals)
	@echo "$(CYAN)Starting development servers...$(NC)"
	@echo ""
	@echo "$(CYAN)Open another terminal and run:$(NC)"
	@echo "  $(GREEN)make frontend-dev$(NC)"
	@echo ""
	@echo "$(CYAN)Starting backend...$(NC)"
	@echo ""
	@make backend-dev

dev-docker: docker-up ## Start development with Docker
	@echo "$(GREEN)✓ Development environment running with Docker$(NC)"

# ============================================================================
# DATABASE & MIGRATIONS
# ============================================================================

db-migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations...$(NC)"
	cd backend && poetry run alembic upgrade head
	@echo "$(GREEN)✓ Migrations applied$(NC)"

db-migrate-create: ## Create a new migration (requires MESSAGE variable)
	@echo "$(CYAN)Creating migration...$(NC)"
	cd backend && poetry run alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "$(GREEN)✓ Migration created$(NC)"

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "$(RED)WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? (y/n) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f backend/data/controle_financeiro.db; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	else \
		echo "$(CYAN)Cancelled$(NC)"; \
	fi

# ============================================================================
# SECURITY & QUALITY
# ============================================================================

security-check: ## Run security checks
	@echo "$(CYAN)Running security checks...$(NC)"
	cd backend && poetry run pip-audit 2>/dev/null || echo "$(RED)pip-audit not installed$(NC)"

check-all: backend-all-checks ## Run all code quality checks

# ============================================================================
# UTILITIES
# ============================================================================

version: ## Show project version
	@echo "Controle Financeiro v1.0.0"
	@echo ""
	@echo "Python $(shell python3 --version 2>/dev/null || echo 'not installed')"
	@echo "Node $(shell node --version 2>/dev/null || echo 'not installed')"
	@echo "Poetry $(shell poetry --version 2>/dev/null || echo 'not installed')"

status: ## Show project status
	@echo "$(CYAN)Backend:$(NC)"
	@if [ -d "backend/.venv" ] || [ -f "backend/poetry.lock" ]; then \
		echo "  $(GREEN)✓ Installed$(NC)"; \
	else \
		echo "  $(RED)✗ Not installed$(NC)"; \
	fi
	@echo "$(CYAN)Frontend:$(NC)"
	@if [ -d "frontend/node_modules" ]; then \
		echo "  $(GREEN)✓ Installed$(NC)"; \
	else \
		echo "  $(RED)✗ Not installed$(NC)"; \
	fi
	@echo "$(CYAN)Docker:$(NC)"
	@if docker ps -a 2>/dev/null | grep -q controle-financeiro; then \
		echo "  $(GREEN)✓ Containers exist$(NC)"; \
	else \
		echo "  $(RED)✗ No containers$(NC)"; \
	fi
