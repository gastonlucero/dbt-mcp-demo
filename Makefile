.PHONY: help dev dev-build dbt-shell dbt-run dbt-test dbt-docs dbt-debug dbt-parse \
        logs logs-dbt logs-mcp logs-postgres stop down clean info \
        all shell run test docs

COMPOSE := docker-compose -f docker/docker-compose.yml
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help message
	@echo "$(BLUE)dbt Analytics + MCP Server$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev              # Start dev environment"
	@echo "  make dev-build        # Build and start dev environment"
	@echo "  make dbt-shell        # Open dbt container shell"
	@echo ""
	@echo "$(GREEN)dbt Commands:$(NC)"
	@echo "  make dbt-run          # Run dbt models"
	@echo "  make dbt-test         # Run dbt tests"
	@echo "  make dbt-docs         # Generate dbt documentation"
	@echo "  make dbt-debug        # Debug dbt connection"
	@echo "  make dbt-parse        # Parse dbt models"
	@echo ""
	@echo "$(GREEN)Logs:$(NC)"
	@echo "  make logs             # Logs from all services"
	@echo "  make logs-dbt         # dbt logs"
	@echo "  make logs-mcp         # MCP server logs"
	@echo "  make logs-postgres    # PostgreSQL logs"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make stop             # Stop all services"
	@echo "  make down             # Stop and remove services"
	@echo "  make clean            # Remove services, volumes"
	@echo "  make info             # Show service status"
	@echo ""

dev: ## Start dev environment
	@echo "$(GREEN)Starting dev environment...$(NC)"
	cd docker && docker-compose up

dev-build: ## Build and start dev environment
	@echo "$(GREEN)Building dev environment...$(NC)"
	cd docker && docker-compose up --build

dbt-shell: ## Open dbt shell
	@echo "$(GREEN)Opening dbt shell...$(NC)"
	docker exec -it dbt-dev bash

dbt-run: ## Run dbt models
	docker exec dbt-dev dbt run

dbt-test: ## Run dbt tests
	docker exec dbt-dev dbt test

dbt-docs: ## Generate dbt documentation
	docker exec dbt-dev dbt docs generate
	@echo "$(YELLOW)To view docs, run:$(NC) docker exec dbt-dev dbt docs serve --host 0.0.0.0"

dbt-debug: ## Debug dbt connection
	docker exec dbt-dev dbt debug

dbt-parse: ## Parse dbt models
	docker exec dbt-dev dbt parse

logs: ## Show logs from all services
	$(COMPOSE) logs -f

logs-dbt: ## Show dbt logs
	$(COMPOSE) logs -f dbt

logs-mcp: ## Show MCP server logs
	$(COMPOSE) logs -f mcp-server

logs-postgres: ## Show PostgreSQL logs
	$(COMPOSE) logs -f postgres

stop: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	$(COMPOSE) stop

down: ## Stop and remove services
	@echo "$(YELLOW)Removing services...$(NC)"
	$(COMPOSE) down

clean: ## Remove services, volumes, images
	@echo "$(RED)Cleaning up...$(NC)"
	$(COMPOSE) down -v
	@echo "$(GREEN)Done$(NC)"

info: ## Show service status
	@echo "$(BLUE)Services:$(NC)"
	$(COMPOSE) ps
	@echo ""
	@echo "$(BLUE)Networks:$(NC)"
	docker network ls | grep dbt-mcp
	@echo ""
	@echo "$(BLUE)Volumes:$(NC)"
	docker volume ls | grep postgres

# Aliases
all: dev-build
shell: dbt-shell
run: dbt-run
test: dbt-test
docs: dbt-docs

.DEFAULT_GOAL := help
