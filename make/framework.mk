# Framework Management Targets
# Start, stop, list, and test benchmark frameworks

.PHONY: framework-list framework-start framework-stop framework-smoke

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
