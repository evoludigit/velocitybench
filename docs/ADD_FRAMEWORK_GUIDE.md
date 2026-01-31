# Adding a New Framework to VelocityBench

This guide walks you through adding a complete framework implementation to VelocityBench. Follow each section carefully to ensure consistency across the project.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Create Framework Directory](#step-1-create-framework-directory)
4. [Step 2: Implement Endpoints](#step-2-implement-endpoints)
5. [Step 3: Add Tests](#step-3-add-tests)
6. [Step 4: Add Health Checks](#step-4-add-health-checks)
7. [Step 5: Register Framework](#step-5-register-framework)
8. [Step 6: Docker Configuration](#step-6-docker-configuration)
9. [Step 7: Documentation](#step-7-documentation)
10. [Step 8: Verification](#step-8-verification)
11. [Troubleshooting](#troubleshooting)

---

## Overview

VelocityBench benchmarks framework implementations across two API types:
- **REST APIs** - Traditional HTTP endpoints
- **GraphQL APIs** - Query-based graph endpoints

Each framework implementation must provide endpoints for querying a standardized database schema (the Trinity Pattern).

**Before starting**: Decide which API type(s) your framework implements:
- **REST only** - POST/GET endpoints following REST conventions
- **GraphQL only** - Single `/graphql` endpoint with query/mutation support
- **Both** - Implement both API types in parallel

---

## Prerequisites

### Required
- VelocityBench repository cloned locally
- Docker and Docker Compose installed
- Language toolchain for your framework (Python, Node, Go, Rust, Java, PHP, Ruby, or C#)
- Git

### Knowledge
- Your framework's basic setup (how to create a project, add dependencies, run locally)
- Understanding of the Trinity Pattern schema (see [docs/api/SCHEMA.md](../docs/api/SCHEMA.md))
- Understanding of VelocityBench API specifications (see [docs/api/REST.md](../docs/api/REST.md) and [docs/api/GraphQL.md](../docs/api/GraphQL.md))

### Time Required
- **REST framework**: 3-4 hours
- **GraphQL framework**: 4-5 hours
- **Both**: 6-8 hours

---

## Step 1: Create Framework Directory

### 1a. Create Directory Structure

```bash
cd /home/lionel/code/velocitybench/frameworks
mkdir -p your-framework-name/{tests,src}
cd your-framework-name
```

Replace `your-framework-name` with your framework (e.g., `express-rest`, `django-rest`, etc.).

### 1b. Create Language-Specific Setup

**For Python**:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Create dependency files
touch requirements.txt requirements-dev.txt pyproject.toml

# Create main application files
touch src/__init__.py src/app.py src/models.py src/schema.py
```

**For Node.js**:
```bash
# Initialize npm project
npm init -y

# Create main files
mkdir -p src
touch src/app.js src/schema.graphql .env.example
```

**For Go**:
```bash
# Initialize Go module
go mod init github.com/velocitybench/your-framework-name
mkdir -p cmd/server
touch cmd/server/main.go
```

**For Rust**:
```bash
# Initialize Cargo project
cargo init --name your-framework-name
```

**For Java**:
```bash
# Create directory structure
mkdir -p src/{main,test}/{java/com/velocitybench/{model,service,controller},resources}
```

### 1c. Create Standard Files

Create the following files in your framework directory:

**`.gitignore`**:
```
.venv
venv
__pycache__/
*.pyc
.pytest_cache/
node_modules/
.env
.env.local
dist/
build/
target/
.cargo/
.idea/
.vscode/
*.log
```

**`.env.example`**:
```
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/velocitybench
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_NAME=velocitybench
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Framework Configuration
HOST=localhost
PORT=8000
DEBUG=False
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
```

**`README.md`**:
```markdown
# VelocityBench: [Framework Name] Implementation

[Brief description of framework and implementation]

## Quick Start

### Prerequisites
- [Language version]
- PostgreSQL client
- Docker (optional, for database)

### Setup

1. Clone repository and navigate to this directory
2. Create virtual environment (language-specific)
3. Copy `.env.example` to `.env`
4. Install dependencies
5. Start database: `docker-compose up -d postgres`
6. Run application: `[start command]`
7. Verify: `curl http://localhost:8000/health`

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T12:00:00Z"
}
```

### Testing
```bash
[test command]
```

## API Endpoints

### REST Endpoints
- `GET /health` - Health check
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user with posts
- etc.

### GraphQL Endpoint
- `POST /graphql` - GraphQL queries and mutations

## Project Structure
[Describe your directory layout]

## Framework Notes
[Any implementation-specific notes]
```

---

## Step 2: Implement Endpoints

### 2a. Understand the Schema

Review the Trinity Pattern database schema:
```bash
cat ../../docs/api/SCHEMA.md
```

The schema includes:
- **Users** - Basic user information
- **Posts** - User-authored posts
- **Comments** - Comments on posts
- **Tags** - Post categorization

### 2b. Implement REST Endpoints

Implement these endpoints following REST conventions:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check probe |
| GET | `/api/users` | List all users (with pagination) |
| GET | `/api/users/{id}` | Get user + their posts (no comments) |
| POST | `/api/users` | Create user |
| GET | `/api/users/{id}/posts` | Get user's posts with comments |
| GET | `/api/posts` | List all posts (paginated) |
| GET | `/api/posts/{id}` | Get post with comments and author |
| POST | `/api/posts` | Create post |
| GET | `/api/comments` | List comments (paginated) |
| POST | `/api/comments` | Create comment |

See [docs/api/REST.md](../docs/api/REST.md) for detailed specifications.

**Example Request/Response**:
```bash
# Get user with posts
curl http://localhost:8000/api/users/1

# Expected response
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "posts": [
    {
      "id": 101,
      "title": "First Post",
      "content": "...",
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ]
}
```

### 2c. Implement GraphQL Schema

Create GraphQL types matching the REST API structure:

**Example types**:
```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
  tags: [String!]!
  createdAt: DateTime!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users(limit: Int, offset: Int): [User!]!
  post(id: ID!): Post
  posts(limit: Int, offset: Int): [Post!]!
  comments(limit: Int, offset: Int): [Comment!]!
}

type Mutation {
  createUser(name: String!, email: String!): User!
  createPost(userId: ID!, title: String!, content: String!): Post!
  createComment(postId: ID!, userId: ID!, content: String!): Comment!
}
```

See [docs/api/GraphQL.md](../docs/api/GraphQL.md) for full specification.

### 2d. Database Connection

Create a database connection module:

**Python Example**:
```python
# src/db.py
import asyncpg
import os

async def get_db_pool():
    return await asyncpg.create_pool(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', 5433)),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', 'postgres'),
        database=os.getenv('DATABASE_NAME', 'velocitybench'),
        min_size=5,
        max_size=20
    )
```

---

## Step 3: Add Tests

### 3a. Create Test Directory

```bash
mkdir -p tests
touch tests/__init__.py tests/conftest.py
```

### 3b. Create conftest.py

Set up shared test fixtures:

**Python Example** (tests/conftest.py):
```python
import pytest
import asyncpg
import os
from src.app import app  # your app factory

@pytest.fixture
async def db_pool():
    """Database connection pool for tests"""
    pool = await asyncpg.create_pool(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', 5433)),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', 'postgres'),
        database=os.getenv('DATABASE_NAME', 'velocitybench'),
    )
    yield pool
    await pool.close()

@pytest.fixture
async def client(db_pool):
    """Test client for API"""
    async with TestClient(app) as client:
        yield client
```

### 3c. Implement Tests

Create test files for each endpoint group:

**Test structure**:
```
tests/
├── __init__.py
├── conftest.py
├── test_health.py         # Health check tests
├── test_users.py          # User endpoints
├── test_posts.py          # Post endpoints
├── test_comments.py       # Comment endpoints
├── test_graphql.py        # GraphQL query tests
└── test_performance.py    # N+1 and other checks
```

**Minimum test coverage**: 70% of code

**Example test**:
```python
# tests/test_users.py
import pytest

@pytest.mark.asyncio
async def test_get_user_with_posts(client, db_pool):
    """Test GET /api/users/{id} returns user with posts"""
    response = await client.get("/api/users/1")

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 1
    assert 'posts' in data
    assert isinstance(data['posts'], list)

@pytest.mark.asyncio
async def test_create_user(client, db_pool):
    """Test POST /api/users creates user"""
    response = await client.post(
        "/api/users",
        json={"name": "Test User", "email": "test@example.com"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data['name'] == "Test User"
```

### 3d. Run Tests Locally

```bash
# Python
pytest tests/ -v --cov=src

# Node.js
npm test

# Go
go test ./...

# Rust
cargo test
```

---

## Step 4: Add Health Checks

VelocityBench uses Kubernetes-compatible health checks.

### 4a. Implement Health Endpoint

Return JSON with status, timestamp, and version:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T12:00:00Z",
  "uptime": 3600,
  "version": "0.1.0",
  "database": {
    "connected": true,
    "latency_ms": 2.5
  }
}
```

**Python Example**:
```python
@app.get("/health")
async def health_check(db_pool):
    try:
        async with db_pool.acquire() as conn:
            start = time.time()
            await conn.fetchval("SELECT 1")
            latency = (time.time() - start) * 1000

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime": int(time.time() - app.start_time),
            "version": "0.1.0",
            "database": {
                "connected": True,
                "latency_ms": round(latency, 2)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }, 503
```

### 4b. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

---

## Step 5: Register Framework

### 5a. Update framework_registry.yaml

Add your framework to the registry:

```bash
# Edit tests/qa/framework_registry.yaml
```

Add entry:
```yaml
your-framework-name:
  type: "rest"  # or "graphql" or "both"
  language: "python"  # or appropriate language
  enabled: true
  port: 8000
  base_url: "http://localhost:8000"
  endpoints:
    rest:
      health: "/health"
      users: "/api/users"
      posts: "/api/posts"
      comments: "/api/comments"
    graphql:
      url: "/graphql"  # if applicable
  features:
    async: true
    orm: false
    subscriptions: false
```

### 5b. Verify Registration

```bash
python tests/qa/framework_validator.py --framework your-framework-name
```

---

## Step 6: Docker Configuration

### 6a. Create Dockerfile

**Python Example**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV DATABASE_HOST=postgres
ENV DATABASE_PORT=5432
ENV PORT=8000

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6b. Update docker-compose.yml

Add service to `docker-compose.yml`:

```yaml
services:
  your-framework-name:
    build:
      context: frameworks/your-framework-name
      dockerfile: Dockerfile
    container_name: your-framework-name
    ports:
      - "8000:8000"
    environment:
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: velocitybench
      DATABASE_USER: postgres
      DATABASE_PASSWORD: postgres
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 2s
      retries: 3
```

### 6c. Assign Unique Port

Choose an unused port from this range:
- Python frameworks: 8000-8010
- Node frameworks: 3000, 4000-4010
- Go frameworks: 4010-4020
- Rust frameworks: 8015-8020
- Java frameworks: 8010-8015
- PHP frameworks: 8020-8030
- Ruby frameworks: 8012-8014
- C#/.NET: 8100-8110

Update `docker-compose.yml` with your chosen port.

---

## Step 7: Documentation

### 7a. Write Framework README

See Step 1c for README template. Include:
- Quick start instructions
- Health check example
- API endpoint documentation
- Framework-specific notes
- Known limitations or optimizations

### 7b. Document Implementation Decisions

If your framework has unique decisions, add to ADRs:

```bash
# Create if needed
touch ../../docs/adr/ADR-0XX-[your-framework-name].md
```

Example:
```markdown
# ADR-0XX: [Framework Name] ORM Decision

## Context
[Explain why you chose this ORM]

## Decision
[What you decided]

## Consequences
[Benefits and trade-offs]
```

---

## Step 8: Verification

### 8a. Checklist

- [ ] Framework directory created with standard structure
- [ ] All endpoints implemented (REST or GraphQL)
- [ ] Database connection working
- [ ] Health check endpoint returns correct format
- [ ] Tests written (minimum 70% coverage)
- [ ] Tests pass locally
- [ ] Framework registered in `framework_registry.yaml`
- [ ] Docker image builds successfully
- [ ] Docker container starts and responds to health check
- [ ] README.md is complete and accurate
- [ ] `.env.example` file present
- [ ] `.gitignore` file present
- [ ] Pre-commit hooks pass (if enabled)

### 8b. Local Testing

```bash
# 1. Build Docker image
docker build -t your-framework-name frameworks/your-framework-name

# 2. Start database
docker-compose up -d postgres

# 3. Run container
docker run --rm \
  -p 8000:8000 \
  -e DATABASE_HOST=host.docker.internal \
  --name your-framework-name \
  your-framework-name

# 4. Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/users

# 5. Run integration tests
./tests/integration/smoke-test.sh --framework=your-framework-name
```

### 8c. CI/CD Verification

Update `.github/workflows/unit-tests.yml` to include your framework:

```yaml
strategy:
  matrix:
    framework: [existing-frameworks, your-framework-name]
```

---

## Troubleshooting

### Common Issues

#### Database Connection Fails
```
Error: could not connect to server
```

**Solutions**:
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Check DATABASE_URL environment variable
- Verify credentials in `.env`

#### Port Already in Use
```
Error: Address already in use
```

**Solution**:
```bash
lsof -i :8000
kill -9 <PID>
```

Or choose a different port in `docker-compose.yml`

#### Health Check Timeout
```
Health check failed after 30s
```

**Solutions**:
- Increase healthcheck timeout in docker-compose.yml
- Check application startup logs: `docker logs your-framework-name`
- Ensure all dependencies are installed

#### Framework Not Appearing in Registry
```
Framework not found in registry
```

**Solutions**:
- Verify entry in `tests/qa/framework_registry.yaml`
- Check YAML syntax: `python -m yaml framework_registry.yaml`
- Ensure port matches docker-compose.yml

### Getting Help

1. Check framework READMEs in `frameworks/*/README.md`
2. Review similar framework implementations
3. See [DEVELOPMENT.md](DEVELOPMENT.md) for general guidance
4. Create issue on GitHub with:
   - Framework name and error message
   - Steps to reproduce
   - Output of `docker logs your-framework-name`

---

## Next Steps

After adding your framework:

1. **Performance Testing**: Include in performance benchmarks
2. **Regression Testing**: Add to CI/CD pipeline
3. **Documentation**: Publish implementation guide
4. **Community**: Share implementation on GitHub Discussions

---

## Example Implementations

See these frameworks for reference:

- **Python REST**: `frameworks/fastapi-rest/`
- **Python GraphQL**: `frameworks/strawberry/`
- **Node.js REST**: `frameworks/express-rest/`
- **Node.js GraphQL**: `frameworks/apollo-server/`
- **Go GraphQL**: `frameworks/go-gqlgen/`
- **Rust GraphQL**: `frameworks/async-graphql/`

---

**Questions?** See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.

Good luck! 🚀
