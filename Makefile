.PHONY: help blog-all blog-pattern blog-fraisier blog-webhooks blog-git-providers blog-cqrs blog-history blog-multi-provider \
	blog-list blog-clean venv-check venv-setup framework-start framework-stop framework-smoke framework-list

# Project paths
PROJECT_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV_PATH := $(PROJECT_ROOT)venv
VENV_PYTHON := $(VENV_PATH)/bin/python
VENV_ACTIVATE := $(VENV_PATH)/bin/activate
GENERATOR_DIR := $(PROJECT_ROOT)database/seed-data/generator
GENERATOR_SCRIPT := generate_blog_vllm.py
OUTPUT_DIR := $(PROJECT_ROOT)database/seed-data/output/blog

# Default help
help:
	@echo "======================================================================"
	@echo "VelocityBench - Framework Benchmarking Suite"
	@echo "======================================================================"
	@echo ""
	@echo "Framework Commands:"
	@echo "  make framework-list             - List all available frameworks"
	@echo "  make framework-start FRAMEWORK=<name>  - Start a framework"
	@echo "  make framework-stop FRAMEWORK=<name>   - Stop a framework"
	@echo "  make framework-smoke            - Run smoke tests on running frameworks"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-up                      - Start PostgreSQL database"
	@echo "  make db-down                    - Stop PostgreSQL database"
	@echo ""
	@echo "Blog Generation Commands:"
	@echo "  make blog-all                   - Generate ALL blog posts for all patterns"
	@echo "  make blog-fraisier              - Generate Fraisier deployment pattern blogs"
	@echo "  make blog-webhooks              - Generate webhook deployment blogs"
	@echo "  make blog-git-providers         - Generate Git provider abstraction blogs"
	@echo "  make blog-cqrs                  - Generate CQRS deployment pattern blogs"
	@echo "  make blog-history               - Generate deployment history blogs"
	@echo "  make blog-multi-provider        - Generate multi-Git-provider blogs"
	@echo "  make blog-multi-env             - Generate multi-environment blogs"
	@echo ""
	@echo "Individual Pattern Commands:"
	@echo "  make blog-pattern PATTERN=<id> TYPE=<type> DEPTH=<depth>"
	@echo "    PATTERN: pattern ID (required)"
	@echo "    TYPE:    tutorial|troubleshooting|reference|comparison (default: tutorial)"
	@echo "    DEPTH:   beginner|intermediate|advanced (default: beginner)"
	@echo ""
	@echo "List & Info Commands:"
	@echo "  make blog-list                  - List all discovered patterns"
	@echo "  make venv-check                 - Check if virtualenv is set up"
	@echo "  make venv-setup                 - Create virtualenv if needed"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  make blog-clean                 - Clean generated blog files"
	@echo ""
	@echo "Examples:"
	@echo "  make framework-start FRAMEWORK=fraiseql  # Start FraiseQL on port 4000"
	@echo "  make framework-smoke                     # Test running frameworks"
	@echo "  make blog-fraisier                       # Generate Fraisier blogs"
	@echo ""
	@echo "======================================================================"

# Check if virtualenv exists
venv-check:
	@if [ -d "$(VENV_PATH)" ]; then \
		echo "✓ Virtual environment found at $(VENV_PATH)"; \
		echo "✓ Python: $$($(VENV_PYTHON) --version)"; \
	else \
		echo "✗ Virtual environment NOT found at $(VENV_PATH)"; \
		echo "  Run: make venv-setup"; \
		exit 1; \
	fi

# Setup virtualenv if it doesn't exist
venv-setup:
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_PATH); \
		$(VENV_PYTHON) -m pip install --upgrade pip; \
		echo "Installing dependencies..."; \
		$(VENV_PYTHON) -m pip install requests pyyaml; \
		echo "✓ Virtual environment ready"; \
	else \
		echo "✓ Virtual environment already exists"; \
	fi

# Generate all blog posts
blog-all: venv-check
	@echo "======================================================================"
	@echo "Generating ALL blog posts from patterns (this will take a while...)"
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) $(GENERATOR_SCRIPT) --all
	@echo "======================================================================"
	@echo "✓ Blog generation complete!"
	@echo "Output directory: $(OUTPUT_DIR)"
	@echo "======================================================================"

# Generate for fraisier-deployment-orchestration pattern
blog-fraisier: venv-check
	@echo "======================================================================"
	@echo "Generating Fraisier Deployment Orchestration blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type reference
	@echo "======================================================================"
	@echo "✓ Fraisier deployment pattern blogs generated!"
	@echo "======================================================================"

# Generate for webhook-event-driven-deployment pattern
blog-webhooks: venv-check
	@echo "======================================================================"
	@echo "Generating Webhook Event-Driven Deployment blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type reference
	@echo "======================================================================"
	@echo "✓ Webhook deployment pattern blogs generated!"
	@echo "======================================================================"

# Generate for git-provider-abstraction pattern
blog-git-providers: venv-check
	@echo "======================================================================"
	@echo "Generating Git Provider Abstraction blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type reference
	@echo "======================================================================"
	@echo "✓ Git provider abstraction pattern blogs generated!"
	@echo "======================================================================"

# Generate for fraisier-cqrs-deployment pattern
blog-cqrs: venv-check
	@echo "======================================================================"
	@echo "Generating CQRS Deployment Pattern blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type reference
	@echo "======================================================================"
	@echo "✓ CQRS deployment pattern blogs generated!"
	@echo "======================================================================"

# Generate for deployment-history-tracking pattern
blog-history: venv-check
	@echo "======================================================================"
	@echo "Generating Deployment History Tracking blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type reference
	@echo "======================================================================"
	@echo "✓ Deployment history pattern blogs generated!"
	@echo "======================================================================"

# Generate for fraisier-multi-git-provider pattern
blog-multi-provider: venv-check
	@echo "======================================================================"
	@echo "Generating Multi-Git-Provider blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type reference
	@echo "======================================================================"
	@echo "✓ Multi-Git-provider pattern blogs generated!"
	@echo "======================================================================"

# Generate for fraisier-multi-environment pattern
blog-multi-env: venv-check
	@echo "======================================================================"
	@echo "Generating Multi-Environment blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type reference
	@echo "======================================================================"
	@echo "✓ Multi-environment pattern blogs generated!"
	@echo "======================================================================"

# Generate for specific pattern with arguments
blog-pattern: venv-check
	@if [ -z "$(PATTERN)" ]; then \
		echo "Error: PATTERN is required"; \
		echo "Usage: make blog-pattern PATTERN=<id> [TYPE=<type>] [DEPTH=<depth>]"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@TYPE=$${TYPE:-tutorial}; \
	DEPTH=$${DEPTH:-beginner}; \
	echo "Generating blog for pattern: $(PATTERN)"; \
	echo "Type: $$TYPE, Depth: $$DEPTH"; \
	cd $(GENERATOR_DIR) && $(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern $(PATTERN) --type $$TYPE --depth $$DEPTH

# List all patterns
blog-list: venv-check
	@echo "======================================================================"
	@echo "Discovering patterns in corpus..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) -c "\
	from pathlib import Path; \
	import yaml; \
	corpus = Path('$(PROJECT_ROOT)database/seed-data/corpus/patterns'); \
	patterns = {}; \
	for cat_dir in corpus.iterdir(): \
		if cat_dir.is_dir(): \
			for yaml_file in cat_dir.glob('*.yaml'): \
				pattern_id = yaml_file.stem; \
				patterns[pattern_id] = cat_dir.name; \
	print(f'Total patterns: {len(patterns)}'); \
	print('\\nFraisier patterns:'); \
	for pid in sorted(patterns.keys()): \
		if 'fraisier' in pid or 'webhook' in pid or 'git-provider' in pid or 'deployment-history' in pid: \
			print(f'  - {pid} ({patterns[pid]})');"
	@echo "======================================================================"

# Clean generated blog files
blog-clean:
	@echo "Cleaning generated blog files..."
	@if [ -d "$(OUTPUT_DIR)" ]; then \
		find $(OUTPUT_DIR) -type f -name "*.md" -delete; \
		echo "✓ Cleaned: $(OUTPUT_DIR)"; \
	fi
	@echo "Done."

# Show venv info
venv-info:
	@echo "Virtual Environment Info:"
	@echo "  Path: $(VENV_PATH)"
	@echo "  Python: $(VENV_PYTHON)"
	@echo "  Activate: source $(VENV_ACTIVATE)"

.PHONY: help blog-all blog-pattern blog-fraisier blog-webhooks blog-git-providers blog-cqrs blog-history blog-multi-provider blog-multi-env blog-list blog-clean venv-check venv-setup venv-info \
	framework-start framework-stop framework-smoke framework-list db-up db-down

# ======================================================================
# Framework Management Commands
# ======================================================================

# List all available frameworks
framework-list:
	@echo "======================================================================"
	@echo "Available Frameworks (use with framework-start, framework-stop, framework-smoke)"
	@echo "======================================================================"
	@echo ""
	@echo "GraphQL Frameworks (port 4000):"
	@echo "  Tier 1 - Production Ready:"
	@echo "    fraiseql        - FraiseQL (Python, JSONB pre-composition)"
	@echo "    strawberry      - Strawberry GraphQL (Python)"
	@echo "    graphene        - Graphene (Python)"
	@echo "    apollo-server   - Apollo Server (Node.js)"
	@echo "    ariadne         - Ariadne (Python, schema-first)"
	@echo "    asgi-graphql    - ASGI GraphQL (Python, raw graphql-core)"
	@echo "    graphql-yoga    - GraphQL Yoga (Node.js)"
	@echo "    mercurius       - Mercurius (Node.js, Fastify)"
	@echo "    express-graphql - Express GraphQL (Node.js)"
	@echo "    go-gqlgen       - gqlgen (Go, code-gen)"
	@echo "    graphql-go      - graphql-go (Go, reflection)"
	@echo "    async-graphql   - async-graphql (Rust)"
	@echo "    juniper         - Juniper (Rust)"
	@echo "    hanami          - Hanami (Ruby)"
	@echo "    webonyx-graphql-php - webonyx/graphql-php (PHP)"
	@echo "    spring-graphql  - Spring GraphQL (Java)"
	@echo "    micronaut-graphql - Micronaut GraphQL (Java)"
	@echo "    quarkus-graphql - Quarkus GraphQL (Java)"
	@echo "    play-graphql    - Play/Sangria (Scala)"
	@echo "    csharp-dotnet   - HotChocolate (C#/.NET)"
	@echo "    hasura          - Hasura (auto-generated)"
	@echo "    postgraphile    - PostGraphile (auto-generated)"
	@echo ""
	@echo "  Tier 2 - N+1 Demonstration:"
	@echo "    apollo-orm      - Apollo ORM (naive)"
	@echo ""
	@echo "REST Frameworks (port 8080):"
	@echo "    fastapi-rest    - FastAPI (Python)"
	@echo "    flask-rest      - Flask (Python)"
	@echo "    express-rest    - Express (Node.js)"
	@echo "    gin-rest        - Gin (Go)"
	@echo "    actix-web-rest  - Actix-web (Rust)"
	@echo "    spring-boot     - Spring Boot (Java)"
	@echo "    php-laravel     - Laravel (PHP)"
	@echo ""
	@echo "======================================================================"
	@echo "Usage:"
	@echo "  make framework-start FRAMEWORK=fraiseql    # Start a framework"
	@echo "  make framework-stop FRAMEWORK=fraiseql     # Stop a framework"
	@echo "  make framework-smoke                       # Run smoke test on all running"
	@echo "======================================================================"

# Start a specific framework (only one GraphQL or REST at a time recommended)
framework-start:
	@if [ -z "$(FRAMEWORK)" ]; then \
		echo "Error: FRAMEWORK is required"; \
		echo "Usage: make framework-start FRAMEWORK=<name>"; \
		echo "Run 'make framework-list' to see available frameworks"; \
		exit 1; \
	fi
	@echo "Starting framework: $(FRAMEWORK)..."
	docker compose --profile $(FRAMEWORK) up -d
	@echo "Framework $(FRAMEWORK) started. Waiting for health check..."
	@sleep 5
	@$(MAKE) framework-smoke 2>/dev/null || echo "Health check pending..."

# Stop a specific framework
framework-stop:
	@if [ -z "$(FRAMEWORK)" ]; then \
		echo "Error: FRAMEWORK is required"; \
		echo "Usage: make framework-stop FRAMEWORK=<name>"; \
		exit 1; \
	fi
	@echo "Stopping framework: $(FRAMEWORK)..."
	docker compose --profile $(FRAMEWORK) down

# Run smoke test on all running frameworks
framework-smoke:
	@echo "Running smoke tests..."
	@bash $(PROJECT_ROOT)tests/integration/smoke-test.sh

# ======================================================================
# Database Commands
# ======================================================================

# Start database only
db-up:
	@echo "Starting PostgreSQL database..."
	docker compose up -d postgres
	@echo "Waiting for database to be healthy..."
	@sleep 3
	@docker compose exec postgres pg_isready -U benchmark || echo "Database starting up..."

# Stop database
db-down:
	@echo "Stopping PostgreSQL database..."
	docker compose down postgres
