# Codebase Navigation Guide

## Overview

VelocityBench is a polyglot benchmarking suite with 35+ framework implementations across 10+ programming languages. This guide helps agents navigate the codebase efficiently to understand, modify, and extend it.

---

## Directory Structure

```
velocitybench/
├── database/                    # Database schema, migrations, and seeding
├── frameworks/                  # All framework implementations (35+)
│   ├── fastapi-rest/           # Python REST (FastAPI)
│   ├── flask-rest/             # Python REST (Flask)
│   ├── strawberry/             # Python GraphQL (Strawberry)
│   ├── graphene/               # Python GraphQL (Graphene)
│   ├── express-rest/           # Node.js REST (Express)
│   ├── apollo-server/          # Node.js GraphQL (Apollo)
│   ├── gin-rest/               # Go REST (Gin)
│   ├── go-gqlgen/              # Go GraphQL (GraphQL-Go)
│   ├── java-spring-boot/       # Java REST/GraphQL
│   ├── ruby-rails/             # Ruby REST (Rails)
│   ├── php-laravel/            # PHP REST (Laravel)
│   ├── csharp-dotnet/          # C# REST (.NET)
│   ├── rust-actix-web/         # Rust REST (Actix-web)
│   ├── async-graphql/          # Rust GraphQL (Async-graphql)
│   ├── common/                 # Python shared utilities
│   └── shared/                 # Language-specific shared code
├── tests/                       # Integration and QA tests
│   ├── common/                 # Shared test fixtures and factories
│   ├── qa/                     # Cross-framework QA tests
│   └── perf/                   # Performance baseline tests
├── docs/                        # All documentation
├── make/                        # Modular Makefile components
├── .github/                     # GitHub Actions CI/CD
├── docker-compose.yml           # Database and service orchestration
├── pytest.ini                   # Pytest configuration
└── VERSION                      # Current version

```

---

## Key Directories Explained

### `database/` - Data Layer

**Purpose**: PostgreSQL schema, migrations, and test data generation

**Key Files**:
- `schema-template.sql` - Core Trinity Pattern schema (users, posts, comments)
- `data.sql` - Initial seed data
- `init.sql` - Database initialization script
- `pyproject.toml` - Database utilities project (uses uv)

**Key Commands**:
```bash
# Start database
docker-compose up -d postgres

# Seed data
cd database && uv run scripts/seed.py

# Run migrations
cd database && uv run scripts/migrate.py
```

**Agent Entry Points**:
- **Adding columns**: Edit `schema-template.sql`, update framework models
- **Adding tables**: Edit `schema-template.sql`, regenerate models
- **Changing constraints**: Edit `schema-template.sql`, update validation
- **Seed data generation**: See `seed-data/` directory

---

### `frameworks/` - All Implementations

**Purpose**: 35+ framework implementations sharing the same API contract

**Structure for each framework**:
```
frameworks/{framework-name}/
├── main.py              # Python: Entry point (FastAPI, Flask, etc.)
├── app.py               # Alternative entry point
├── src/                 # TypeScript/Go/Rust: Source code
├── main.rs              # Rust: Entry point
├── Makefile             # Build and test commands
├── requirements.txt     # Python: Dependencies
├── requirements-dev.txt # Python: Dev dependencies
├── package.json         # Node.js: Dependencies
├── pyproject.toml       # Modern Python project config
├── .venv/               # Python virtual environment
├── venv/                # Alternative Python venv location
├── common/              # Framework-specific utilities
├── models/              # ORM models or TypeScript types
├── resolvers/           # GraphQL resolvers
├── routes/              # REST endpoints or GraphQL schema
├── middleware/          # Request/response middleware
├── tests/               # Framework-specific tests
│   ├── conftest.py      # Pytest configuration
│   ├── test_*.py        # Test files
│   └── fixtures/        # Test data fixtures
├── database/            # Framework-specific database config
├── docker/              # Dockerfile and build config
├── README.md            # Framework implementation guide
└── docker-compose.yml   # Local dev environment

```

### Python Frameworks

**REST Frameworks** (REST endpoints with include parameters for nested data):
- `fastapi-rest/` - FastAPI (async, OpenAPI)
- `flask-rest/` - Flask (sync, minimal)

**GraphQL Frameworks** (GraphQL queries replacing REST include):
- `strawberry/` - Strawberry (modern, Python dataclass-based)
- `graphene/` - Graphene (mature, Django-style)
- `ariadne/` - Ariadne (schema-first approach)
- `asgi-graphql/` - ASGI-GraphQL (lightweight ASGI)

### TypeScript/Node.js Frameworks

**REST**:
- `express-rest/` - Express (minimal)
- `express-orm/` - Express with Prisma ORM

**GraphQL**:
- `apollo-server/` - Apollo Server (industry standard)
- `express-graphql/` - GraphQL over Express
- `mercurius/` - Fastify GraphQL
- `graphql-yoga/` - Modern GraphQL server

### Go Frameworks

**REST**:
- `gin-rest/` - Gin (high-performance)

**GraphQL**:
- `go-gqlgen/` - GQLGen (code-generated, type-safe)
- `graphql-go/` - Go GraphQL library

### Other Languages

- `java-spring-boot/` - Java (REST and GraphQL)
- `ruby-rails/` - Ruby Rails (REST)
- `php-laravel/` - PHP Laravel (REST)
- `csharp-dotnet/` - C# .NET (REST)
- `rust-actix-web/` - Rust Actix (REST)
- `async-graphql/` - Rust async-graphql (GraphQL)

---

### `frameworks/common/` - Python Shared Code

**Purpose**: Reusable Python utilities for all Python frameworks

**Key Modules**:
- `async_db.py` (13KB) - AsyncDatabase connection pool wrapper
- `config.py` - Configuration management and env var handling
- `health_check.py` - Health check endpoint implementation
- `types.py` - Shared type definitions
- `middleware/` - Shared middleware (health checks, etc.)

**Used by**: FastAPI, Flask, Strawberry, Graphene, Ariadne, ASGI-GraphQL

**Agent Entry Point**: When adding common Python functionality, add here first to avoid duplication across frameworks.

---

### `frameworks/shared/` - Language-Specific Shared Code

**Purpose**: Shared utilities per language (avoiding duplication across frameworks)

**Structure**:
```
frameworks/shared/
├── csharp/          # .NET helpers
├── go/              # Go helpers
├── java/            # Java/Spring Boot helpers
├── php/             # PHP/Laravel helpers
├── ruby/            # Ruby/Rails helpers
├── rust/            # Rust helpers
└── typescript/      # Node.js/TypeScript helpers
```

**Agent Entry Point**: When code is used by multiple frameworks in the same language, add it here.

---

### `tests/` - Test Infrastructure

**Purpose**: Shared test infrastructure and QA tests

**Key Directories**:

#### `tests/common/` - Shared Test Fixtures
```
tests/common/
├── conftest.py              # Global pytest configuration
├── fixtures.py              # db, factory fixtures
├── factory.py               # TestFactory class
├── bulk_factory.py          # BulkFactory class (bulk creation)
├── async_db.py              # AsyncDatabase for async tests
└── types.py                 # Test type definitions
```

**Used by**: All framework tests

**Key Components**:
- `db` fixture: PostgreSQL connection with transaction isolation
- `factory` fixture: Individual entity creation (create_user, create_post, etc.)
- `bulk_factory` fixture: Batch entity creation

#### `tests/qa/` - Cross-Framework QA Tests
```
tests/qa/
├── conftest.py              # QA test configuration
├── test_framework_*.py       # Cross-framework tests
├── framework_registry.yaml   # Framework list and endpoints
└── README.md                 # QA test guide
```

**Tests all frameworks** with same test suite

#### `tests/perf/` - Performance Baseline Tests
```
tests/perf/
├── test_*.py                # Performance benchmark tests
├── baselines/               # Baseline files per version
│   ├── v1.0/                # Version 1.0 baselines
│   ├── current/             # Current baselines
│   └── README.md
├── scripts/
│   ├── generate_baseline.py # Create baseline from results
│   └── compare_baselines.py # Compare two baselines
└── README.md
```

---

## Module Dependency Map

```
┌─────────────────────────────────────┐
│      Database (PostgreSQL)           │
│   - Trinity Pattern schema           │
│   - Users, Posts, Comments, etc.     │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────────────────────────────────────┐
        │   frameworks/common/ (Python Shared)         │
        │   - async_db.py (connection pooling)         │
        │   - config.py (env variables)                │
        │   - health_check.py (health endpoints)       │
        │   - middleware/ (request handling)           │
        └──────┬────────────────────┬──────────────────┘
               │                    │
    ┌──────────▼────────────┐       └────────────────────────────┐
    │  Python Frameworks     │                                    │
    ├────────────────────────┤                                    │
    │ - fastapi-rest/        │       ┌──────────────────────────┐─┴──┐
    │ - flask-rest/          │       │  Non-Python Frameworks  │    │
    │ - strawberry/          │       ├────────────────────────┤    │
    │ - graphene/            │       │ - express-rest/        │    │
    │ - ariadne/             │       │ - apollo-server/       │    │
    │ - asgi-graphql/        │       │ - gin-rest/            │    │
    └────────────┬───────────┘       │ - go-gqlgen/           │    │
                 │                   │ - java-spring-boot/    │    │
                 │                   │ - ruby-rails/          │    │
                 │                   │ - php-laravel/         │    │
                 │                   │ - csharp-dotnet/       │    │
                 │                   │ - rust-actix-web/      │    │
                 │                   │ - async-graphql/       │    │
                 │                   └────────────────────────┘    │
                 │                                                  │
        ┌────────▼────────────────────────────────────────────────┘
        │
        │    (All use same Trinity Pattern schema)
        │    (All implement same API contracts)
        │    (Benchmarked against each other)
        │
        ▼
┌──────────────────────────────────────────┐
│   tests/ - Shared Test Infrastructure    │
├──────────────────────────────────────────┤
│ - tests/common/: fixtures, factories     │
│ - tests/qa/: cross-framework tests       │
│ - tests/perf/: performance baselines     │
└──────────────────────────────────────────┘
```

---

## Entry Points by Task

### Task: Add a New Endpoint to All Frameworks

**Flow**:
1. **Decide operation**: What should the endpoint do?
2. **Define in Trinity Pattern**: If it needs new data, add table/fields to `database/schema-template.sql`
3. **Update DB models**: Update ORM models in each `frameworks/{name}/models/`
4. **Implement REST**: Add endpoint to `fastapi-rest/main.py`, `flask-rest/`, etc.
5. **Implement GraphQL**: Add resolver to `strawberry/main.py`, `graphene/`, etc.
6. **Update shared code**: If common logic, add to `frameworks/common/`
7. **Add tests**: Create tests in `tests/qa/` for all frameworks
8. **Update docs**: Update `docs/API_SCHEMAS.md`

**Files to Touch**:
- `database/schema-template.sql` - Database changes
- `frameworks/*/models/` - ORM model updates
- `frameworks/fastapi-rest/main.py` - REST implementation
- `frameworks/strawberry/main.py` - GraphQL implementation
- `tests/qa/test_*.py` - Test coverage
- `docs/API_SCHEMAS.md` - API documentation

### Task: Fix a Bug in One Framework

**Flow**:
1. **Identify framework**: Which framework has the bug?
2. **Locate code**: Check `frameworks/{name}/main.py` or route files
3. **Run tests**: `cd frameworks/{name} && pytest tests/`
4. **Fix bug**: Modify source code
5. **Verify tests pass**: Run tests again
6. **Check if affects other frameworks**: Is it a pattern used elsewhere?

**Files to Check**:
- `frameworks/{name}/main.py` - Entry point
- `frameworks/{name}/tests/` - Test suite
- `frameworks/common/` - Shared code (if applicable)

### Task: Add Test to Verify Behavior Across All Frameworks

**Flow**:
1. **Understand test need**: What should be tested?
2. **Create test in shared location**: Add to `tests/qa/`
3. **Use framework_registry**: Reference all frameworks from registry
4. **Run test**: `cd tests/qa && pytest test_name.py -v`
5. **Verify all frameworks pass**: Check test results

**Files to Modify**:
- `tests/qa/test_*.py` - Add new test
- `tests/qa/framework_registry.yaml` - Reference if needed

### Task: Change Database Schema

**Flow**:
1. **Edit schema**: Modify `database/schema-template.sql`
2. **Update all models**: Update ORM models in each framework
3. **Create migration**: Add to `database/migrations/` (optional)
4. **Update tests**: If schema changes affect queries
5. **Update documentation**: Update `docs/DATABASE_SCHEMA.md`

**Files to Modify**:
- `database/schema-template.sql` - Core schema
- `frameworks/*/models/` - All ORM models
- `database/migrations/` - Migration files (if present)
- `docs/DATABASE_SCHEMA.md` - Documentation

### Task: Optimize Performance for One Framework

**Flow**:
1. **Profile code**: Identify bottleneck
2. **Modify implementation**: Change code in `frameworks/{name}/`
3. **Run perf tests**: `cd frameworks/{name} && pytest tests/perf/`
4. **Capture baseline**: `make perf-capture-baseline` (from framework dir)
5. **Document improvement**: Update `docs/PERFORMANCE_BASELINE_MANAGEMENT.md`

**Files to Check**:
- `frameworks/{name}/main.py` - Main implementation
- `frameworks/{name}/models/` - ORM models
- `frameworks/common/` - Shared code that affects perf
- `tests/perf/` - Performance tests

### Task: Add Configuration Option

**Flow**:
1. **Decide scope**: Global or framework-specific?
2. **Add env variable**: Define in `.env.example` with documentation
3. **Update config modules**: Modify `frameworks/common/config.py` or framework-specific config
4. **Update startup code**: Check `main.py` in each framework
5. **Document**: Update `docs/DEVELOPMENT.md`

**Files to Modify**:
- `.env.example` - Environment variable definition
- `frameworks/common/config.py` - Configuration parsing
- `frameworks/*/main.py` - Use new config
- `docs/DEVELOPMENT.md` - Configuration documentation

---

## Key Code Patterns

### REST Endpoint Pattern (FastAPI)

```python
# Location: frameworks/fastapi-rest/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    # Query database using pk_user or id
    # Return UserResponse with public fields
    pass

@app.post("/users")
async def create_user(user_data: dict):
    # Validate input using Pydantic
    # Insert into database
    # Return created user
    pass
```

### GraphQL Resolver Pattern (Strawberry)

```python
# Location: frameworks/strawberry/main.py

import strawberry
from typing import Optional

@strawberry.type
class User:
    id: str
    username: str
    email: str

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, id: str) -> Optional[User]:
        # Query database by UUID id
        # Return User or None
        pass

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_user(self, username: str, email: str) -> User:
        # Validate input
        # Insert into database
        # Return created User
        pass
```

### Database Query Pattern

```python
# Location: Any framework

from frameworks.common.async_db import AsyncDatabase

async def get_user(db: AsyncDatabase, user_id: str):
    # Use UUID id for public API queries
    row = await db.fetch_one(
        "SELECT pk_user, id, username, email FROM tb_user WHERE id = $1",
        user_id
    )
    return row

async def get_user_posts(db: AsyncDatabase, user_id: str):
    # Use UUID id, join with posts table
    rows = await db.fetch_all(
        """
        SELECT p.* FROM tb_post p
        JOIN tb_user u ON p.fk_author = u.pk_user
        WHERE u.id = $1
        ORDER BY p.created_at DESC
        """,
        user_id
    )
    return rows
```

### Test Pattern

```python
# Location: tests/common/conftest.py or framework tests

import pytest

def test_user_creation_succeeds(db, factory):
    """User creation with valid data succeeds.

    Given: Valid user data
    When: User is created
    Then: User is persisted with correct values
    """
    user = factory.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert user["id"] is not None  # UUID

def test_post_with_author_includes_author_data(db, factory):
    """Post includes author information in response.

    Given: User and post by that user
    When: Post is queried
    Then: Author information is included
    """
    author = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=author["pk_user"], title="Post")

    # Verify author field
    assert post["fk_author"] == author["pk_user"]
```

---

## Key Files to Modify

### By Task Type

| Task | Primary Files | Secondary Files |
|------|------|----------|
| Add API endpoint | `frameworks/{name}/main.py` | `frameworks/common/` if shared logic |
| Add database field | `database/schema-template.sql` | All `frameworks/*/models/` |
| Fix bug | `frameworks/{name}/main.py` | `tests/qa/` if affects multiple frameworks |
| Optimize perf | `frameworks/{name}/main.py` | `frameworks/common/async_db.py` |
| Change config | `frameworks/common/config.py` | `.env.example`, individual frameworks |
| Add test | `tests/qa/test_*.py` | `tests/common/fixtures.py` (if need new fixtures) |
| Update docs | `docs/API_SCHEMAS.md` | `docs/CODEBASE_NAVIGATION.md` |

---

## Finding Code

### By Concept

| Concept | Location | Examples |
|---------|----------|----------|
| User model | `frameworks/*/models/user.py` or ORM definitions | SQLAlchemy, Pydantic, TypeORM |
| Post endpoint | `frameworks/{name}/main.py` or `routes/` | GET /posts, POST /posts |
| GraphQL resolver | `frameworks/{name}/main.py` or `resolvers/` | Query.post, Mutation.createPost |
| Database query | `frameworks/common/async_db.py` or framework-specific DB module | fetch_one, fetch_all |
| Test fixture | `tests/common/fixtures.py` | db, factory, bulk_factory |
| Configuration | `frameworks/common/config.py` or framework-specific config | get_db_config() |
| Health check | `frameworks/common/health_check.py` | GET /health |
| Middleware | `frameworks/common/middleware/` | request/response processing |

### By Error

| Error | Likely Location | Fix |
|-------|----------|---|
| "User not found" | REST: `frameworks/{name}/main.py` line with `raise HTTPException(404)` | Check query logic |
| "Database connection failed" | `frameworks/common/async_db.py` or framework config | Check DB credentials, pool size |
| "Validation error" | REST: Pydantic model in `main.py`; GraphQL: schema validation | Check field constraints |
| "Test isolation failure" | `tests/common/fixtures.py` or test conftest.py | Check transaction cleanup |
| "Performance regression" | `frameworks/{name}/main.py` or `frameworks/common/` | Check for N+1 queries, indexes |

---

## Useful Commands

### Running Code

```bash
# Start all services
docker-compose up -d

# Start specific framework
cd frameworks/fastapi-rest && make run

# Run tests for framework
cd frameworks/fastapi-rest && pytest tests/ -v

# Run cross-framework tests
cd tests/qa && pytest test_*.py -v

# Run performance tests
cd frameworks/strawberry && pytest tests/perf/ -v
```

### Development Workflow

```bash
# Check code quality
cd frameworks/fastapi-rest && make quality

# Format code
cd frameworks/fastapi-rest && make format

# Type check
cd frameworks/fastapi-rest && make type-check

# Create new framework test
cd tests/qa && pytest test_new_feature.py::test_name -v
```

### Database Operations

```bash
# Reset database
docker-compose down postgres
docker-compose up -d postgres
docker exec postgres psql -U benchmark < database/schema-template.sql

# Seed data
cd database && python scripts/seed.py

# Query database
docker exec postgres psql -U benchmark -d velocitybench_test -c "SELECT * FROM tb_user LIMIT 10;"
```

---

## Agent Guidelines

When navigating the codebase, follow these principles:

1. **Trinity Pattern First**: Always understand `pk_*`, `id`, `fk_*` identifiers
2. **Shared Code**: Check `frameworks/common/` before duplicating
3. **Test First**: Look at tests to understand expected behavior
4. **Documentation**: Reference `docs/` directory for patterns
5. **Consistency**: Follow existing code style in the framework
6. **Cross-Framework**: Consider if change affects multiple frameworks
7. **Database**: Always check `DATABASE_SCHEMA.md` before modifying schema

---

## Related Documentation

- **Database Schema**: `docs/DATABASE_SCHEMA.md` - Complete schema reference
- **API Schemas**: `docs/API_SCHEMAS.md` - REST and GraphQL specifications
- **Architecture**: `docs/ARCHITECTURE.md` - System design overview
- **Testing**: `docs/TESTING_README.md` - Testing infrastructure guide
- **Development**: `docs/DEVELOPMENT.md` - Local development setup

