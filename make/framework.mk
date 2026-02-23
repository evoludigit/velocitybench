# Framework Management Targets
# Start, stop, list, and test benchmark frameworks

# Convenience targets: start/stop the full benchmark stack
up:
	docker compose --profile benchmark up -d

up-medium:
	DATA_VOLUME=medium docker compose --profile benchmark up -d

down:
	docker compose --profile benchmark down



.PHONY: framework-list framework-start framework-stop framework-smoke test-seed smoke-test parity-test bench bench-one bench-all bench-sequential n1-guard validate up up-medium down

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


# Verify seed data row counts
# Usage:
#   make test-seed                  # xs (default) — fixture checks only
#   make test-seed DATA_VOLUME=medium
test-seed:
	@echo "Running seed data verification (DATA_VOLUME=$(DATA_VOLUME:-xs))..."
	DATA_VOLUME=$(DATA_VOLUME) \
	  $(PROJECT_ROOT)tests/qa/.venv/bin/python -m pytest \
	    $(PROJECT_ROOT)tests/qa/test_seed_data.py \
	    -v --tb=short --no-header

# Full smoke test: start all 8 benchmark frameworks and verify health + basic queries
# Usage: make smoke-test [DATA_VOLUME=xs]
smoke-test:
	@echo "Starting benchmark stack (DATA_VOLUME=$(DATA_VOLUME))..."
	DATA_VOLUME=$(DATA_VOLUME) docker compose --profile benchmark up -d
	@echo "Waiting 60s for containers to initialize..."
	@sleep 60
	@echo "Running health + query smoke tests..."
	$(PROJECT_ROOT)tests/qa/.venv/bin/python -m pytest \
	  $(PROJECT_ROOT)tests/qa/test_all_frameworks_health.py \
	  -v --tb=short --no-header
	@echo "Tearing down benchmark stack..."
	docker compose --profile benchmark down

# Cross-framework parity test: verify all frameworks return identical data
# Requires all 8 benchmark services to be running.
# Usage: make parity-test
parity-test:
	@echo "Running cross-framework parity tests..."
	$(PROJECT_ROOT)tests/qa/.venv/bin/python -m pytest \
	  $(PROJECT_ROOT)tests/qa/test_parity.py \
	  -v --tb=short --no-header
	@echo "✓ Parity tests passed"

# Run k6 against a single framework.
# Usage: make bench-one FRAMEWORK=go-gqlgen
bench-one:
	@if [ -z "$(FRAMEWORK)" ]; then \
		echo "Error: FRAMEWORK is required"; \
		echo "Usage: make bench-one FRAMEWORK=<name>"; \
		exit 1; \
	fi
	k6 run --env FRAMEWORK=$(FRAMEWORK) $(PROJECT_ROOT)tests/benchmark/k6/full_suite.js

# Run k6 against all 8 frameworks (parity gate first).
# Usage: make bench-all
bench-all: parity-test
	@echo "Running full k6 benchmark suite..."
	$(PROJECT_ROOT)venv/bin/python $(PROJECT_ROOT)tests/benchmark/run_all.py

# Sequential isolation benchmark (canonical, no k6 required).
# Usage: make bench-sequential [DURATION=20] [CONCURRENCY=40] [FRAMEWORKS="fraiseql-tv gin-rest"]
bench-sequential:
	@echo "Running sequential isolation benchmark..."
	$(PROJECT_ROOT)venv/bin/python $(PROJECT_ROOT)tests/benchmark/bench_sequential.py \
	  $(if $(DURATION),--duration $(DURATION),) \
	  $(if $(CONCURRENCY),--concurrency $(CONCURRENCY),) \
	  $(if $(FRAMEWORKS),--frameworks $(FRAMEWORKS),)

# N+1 query guard: detect DataLoader regressions using pg_stat_statements.
# Run serially against the benchmark stack (no concurrent traffic).
# Usage: make n1-guard
n1-guard:
	@echo "Running N+1 query guard tests..."
	$(PROJECT_ROOT)tests/qa/.venv/bin/python -m pytest \
	  $(PROJECT_ROOT)tests/qa/test_n1_detection.py \
	  -v --tb=short --no-header -p no:randomly
	@echo "✓ N+1 guard passed"

# FraiseQL-specific comparison benchmark (Python threaded, no k6 required).
# Usage: make bench [DURATION=30] [CONCURRENCY=50]
bench: parity-test
	@echo "Parity confirmed. Starting FraiseQL comparison benchmark..."
	$(PROJECT_ROOT)venv/bin/python $(PROJECT_ROOT)tests/benchmark/fraiseql_comparison.py \
	  --duration $(or $(DURATION),30) \
	  --concurrency $(or $(CONCURRENCY),50)

# Full pre-benchmark health check: smoke, parity, N+1 guard.
# Usage: make validate
validate: smoke-test parity-test n1-guard
	@echo "✓ All pre-benchmark validation checks passed"
