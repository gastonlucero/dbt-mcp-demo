.PHONY: help build run shell debug test docs clean

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Docker image name
IMAGE_NAME := dbt-demo-postgres
CONTAINER_NAME := dbt-demo-postgres-run

# PostgreSQL Schema (default: public, override with SCHEMA=<name>)
SCHEMA ?= public

help: ## Show this help message
	@echo "$(BLUE)dbt Project - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Build:$(NC)"
	@echo "  make build              # Build Docker image"
	@echo ""
	@echo "$(GREEN)Interactive Shell:$(NC)"
	@echo "  make shell              # Open interactive dbt shell"
	@echo ""
	@echo "$(GREEN)dbt Commands:$(NC)"
	@echo "  make run                # Run all dbt models (default schema: public)"
	@echo "  make test               # Run dbt tests"
	@echo "  make docs               # Generate dbt documentation"
	@echo "  make debug              # Debug dbt connection"
	@echo "  make parse              # Parse dbt models without running"
	@echo ""
	@echo "$(GREEN)Custom Schema:$(NC)"
	@echo "  SCHEMA=dbt_base make run      # Run models in 'dbt_base' schema"
	@echo "  SCHEMA=dbt_staging make run   # Run models in 'dbt_staging' schema"
	@echo "  SCHEMA=dbt_marts make run     # Run models in 'dbt_marts' schema"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean              # Remove Docker image"
	@echo ""
	@echo "$(YELLOW)Note:$(NC) Default schema is 'public'. Override with SCHEMA=<schema_name>"
	@echo ""

# Base docker run command with environment variables
docker_run_base := docker run --env-file ../.env -e DBT_POSTGRES_SCHEMA=$(SCHEMA) -v $(PWD)/dbt-demo-postgres:/app/dbt-demo-postgres -v $(PWD)/dbt-demo-postgres/profiles.yml --rm $(IMAGE_NAME)
# Interactive version (for shell)
docker_run_interactive := docker run -it --env-file ../.env -e DBT_POSTGRES_SCHEMA=$(SCHEMA) -v $(PWD)/dbt-demo-postgres:/app/dbt-demo-postgres -v $(PWD)/dbt-demo-postgres/profiles.yml --rm $(IMAGE_NAME)

# Build Docker image
build: ## Build dbt Docker image
	@echo "$(GREEN)Building dbt Docker image...$(NC)"
	docker build -f Dockerfile.dbt -t $(IMAGE_NAME) ..

deps:
	$(docker_run_base) dbt deps

create: build deps

# Interactive shell
shell: ## Open interactive dbt shell
	@echo "$(GREEN)Opening dbt interactive shell...$(NC)"
	${docker_run_interactive} bash

# dbt run
run: ## Run all dbt models
	@echo "$(GREEN)Running dbt models in schema: $(SCHEMA)$(NC)"
	${docker_run_base} dbt run

# dbt test
test: ## Run dbt tests
	@echo "$(GREEN)Running dbt tests in schema: $(SCHEMA)$(NC)"
	${docker_run_base} dbt test

# dbt docs
docs: ## Generate dbt documentation
	@echo "$(GREEN)Generating dbt documentation for schema: $(SCHEMA)$(NC)"
	${docker_run_base} dbt docs generate
	@echo "$(YELLOW)To view docs, run inside shell: dbt docs serve --host 0.0.0.0$(NC)"

# dbt debug
debug: ## Debug dbt connection
	@echo "$(GREEN)Debugging dbt connection for schema: $(SCHEMA)$(NC)"
	${docker_run_base} dbt debug

# dbt parse
parse: ## Parse dbt models without running
	@echo "$(GREEN)Parsing dbt models in schema: $(SCHEMA)$(NC)"
	${docker_run_base} dbt parse

# Clean up
clean: ## Remove Docker image
	@echo "$(RED)Removing Docker image...$(NC)"
	docker rmi $(IMAGE_NAME)
	@echo "$(GREEN)Cleanup complete$(NC)"

# Info
info: ## Show image info
	@echo "$(BLUE)Image Name: $(NC)$(IMAGE_NAME)"
	@echo "$(BLUE)Container Name: $(NC)$(CONTAINER_NAME)"
	@echo "$(BLUE)Working Directory: $(NC)/app/dbt/dbt-demo-postgres"

.DEFAULT_GOAL := help
