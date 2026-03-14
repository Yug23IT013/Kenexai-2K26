.PHONY: help build up start stop restart logs shell ps down clean env-setup status test

# Default target
.DEFAULT_GOAL := help

# Color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  Football Analytics Platform - Docker Commands               ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  $(YELLOW)make build$(NC)         # Build Docker image"
	@echo "  $(YELLOW)make start$(NC)         # Start services"
	@echo "  $(YELLOW)make logs$(NC)          # View logs"
	@echo "  $(YELLOW)make status$(NC)        # Check status"
	@echo ""

build: ## Build Docker image
	@echo "$(YELLOW)Building Docker image...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

rebuild: ## Rebuild Docker image without cache
	@echo "$(YELLOW)Rebuilding Docker image without cache...$(NC)"
	@docker-compose build --no-cache
	@echo "$(GREEN)✓ Build complete$(NC)"

up: ## Start services in foreground
	@echo "$(YELLOW)Starting services in foreground...$(NC)"
	@docker-compose up

start: ## Start services in background
	@echo "$(YELLOW)Starting services in background...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@sleep 3
	@make ps

stop: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@docker-compose stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

logs: ## View service logs
	@docker-compose logs -f

logs-all: ## View all logs including backend
	@docker-compose logs -f

logs-backend: ## View backend logs only
	@docker-compose logs -f football-app | grep backend

shell: ## Access container shell
	@echo "$(YELLOW)Accessing container shell...$(NC)"
	@docker-compose exec football-app bash

ps: ## Show running containers
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Service URLs:$(NC)"
	@echo "  $(GREEN)Streamlit$(NC):  http://localhost:8501"
	@echo "  $(GREEN)FastAPI$(NC):    http://localhost:8000/docs"
	@echo ""

down: ## Stop and remove containers
	@echo "$(YELLOW)Stopping and removing containers...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Containers removed$(NC)"

down-volumes: ## Stop and remove containers including volumes
	@echo "$(RED)Removing containers and volumes...$(NC)"
	@docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean: ## Remove images and containers
	@echo "$(RED)Cleaning up Docker resources...$(NC)"
	@docker-compose down -v
	@docker rmi football-analytics-platform:latest 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

env-setup: ## Create .env file from example
	@if [ -f ".env" ]; then \
		echo "$(YELLOW).env file already exists$(NC)"; \
		read -p "Overwrite? (y/N) " -r; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then exit 0; fi; \
	fi
	@cp .env.example .env
	@echo "$(GREEN)✓ Created .env file$(NC)"
	@echo "$(YELLOW)Please edit .env with your credentials:$(NC)"
	@echo "  - SNOWFLAKE_PASSWORD"
	@echo "  - GROQ_API_KEY"

status: ## Check container status
	@echo "$(BLUE)Football Analytics Platform Status$(NC)"
	@echo ""
	@if docker-compose ps | grep -q "running"; then \
		echo "$(GREEN)✓ Services are running$(NC)"; \
		docker-compose ps; \
		echo ""; \
		echo "$(BLUE)Service URLs:$(NC)"; \
		echo "  Streamlit: http://localhost:8501"; \
		echo "  FastAPI:   http://localhost:8000/docs"; \
	else \
		echo "$(RED)✗ Services are not running$(NC)"; \
		echo "Start services with: $(YELLOW)make start$(NC)"; \
	fi

test: ## Test backend connectivity
	@echo "$(YELLOW)Testing backend connectivity...$(NC)"
	@echo ""
	@if docker-compose ps | grep -q "running"; then \
		echo "$(BLUE)Testing Streamlit...$(NC)"; \
		if curl -s http://localhost:8501 > /dev/null; then \
			echo "$(GREEN)✓ Streamlit is responding$(NC)"; \
		else \
			echo "$(RED)✗ Streamlit is not responding$(NC)"; \
		fi; \
		echo "$(BLUE)Testing FastAPI...$(NC)"; \
		if curl -s http://localhost:8000/docs > /dev/null; then \
			echo "$(GREEN)✓ FastAPI is responding$(NC)"; \
		else \
			echo "$(RED)✗ FastAPI is not responding$(NC)"; \
		fi; \
		echo ""; \
		echo "$(GREEN)Service URLs:$(NC)"; \
		echo "  Streamlit: http://localhost:8501"; \
		echo "  FastAPI:   http://localhost:8000/docs"; \
	else \
		echo "$(RED)Services are not running$(NC)"; \
		echo "Start them with: $(YELLOW)make start$(NC)"; \
	fi

prune: ## Remove unused Docker images and containers
	@echo "$(YELLOW)Pruning Docker resources...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✓ Pruning complete$(NC)"

version: ## Show Docker and Docker Compose versions
	@echo "$(BLUE)Docker Versions:$(NC)"
	@docker --version
	@docker-compose --version

.PHONY: push pull
push: ## Push image to registry (requires image name)
	@if [ -z "$(REGISTRY)" ]; then \
		echo "$(RED)Usage: make push REGISTRY=your-registry/image-name$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Pushing to $(REGISTRY)...$(NC)"
	@docker tag football-analytics-platform:latest $(REGISTRY):latest
	@docker push $(REGISTRY):latest
	@echo "$(GREEN)✓ Push complete$(NC)"

pull: ## Pull image from registry
	@if [ -z "$(REGISTRY)" ]; then \
		echo "$(RED)Usage: make pull REGISTRY=your-registry/image-name$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Pulling from $(REGISTRY)...$(NC)"
	@docker pull $(REGISTRY):latest
	@echo "$(GREEN)✓ Pull complete$(NC)"

# Convenience targets
quick-start: env-setup build start status ## Quick start: setup, build, and start

reset: down clean build start ## Reset: clean and rebuild everything

full-reset: down clean env-setup build start status ## Full reset with environment setup

# View specific service information
info-streamlit: ## Show Streamlit service info
	@docker-compose logs -f football-app --tail=50 | grep -E "(Streamlit|localhost|Running)"

info-backend: ## Show FastAPI backend info
	@docker-compose logs -f football-app --tail=50 | grep -E "(FastAPI|uvicorn|port 8000)"

# Useful utilities
install-requirements: ## Install development requirements locally (not in Docker)
	@pip install -r requirements.txt
	@pip install -r streamlit_app/backend/requirements.txt

lint: ## Run Python linting (requires local tools)
	@pylint streamlit_app/ --disable=all --enable=E,F

format: ## Format Python files (requires black)
	@black streamlit_app/

# Documentation
docs: ## Show Docker guide
	@less DOCKER_GUIDE.md

# Development targets
dev: ## Start services in development mode
	@echo "$(YELLOW)Starting in development mode...$(NC)"
	@docker-compose -f docker-compose.yml up

ci: build test ## Run CI checks (build and test)

# Aliases for common operations
b: build ## Alias for 'build'
u: up ## Alias for 'up'
s: start ## Alias for 'start'
st: stop ## Alias for 'stop'
r: restart ## Alias for 'restart'
l: logs ## Alias for 'logs'
p: ps ## Alias for 'ps'

.SILENT:
