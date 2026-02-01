# Phase 3: Framework Blueprints (1 per Language)

## Objective

Create exemplary, idiomatic implementations of FraiseQL integration in Python, TypeScript, Go, Java, and PHP. Each framework acts as a thin proxy to fraiseql-server, demonstrating best practices.

## Success Criteria

- [ ] Python (FastAPI) blueprint complete and tested
- [ ] TypeScript (Express) blueprint complete and tested
- [ ] Go (Gin) blueprint complete and tested
- [ ] Java (Spring Boot) blueprint complete and tested
- [ ] PHP (Laravel) blueprint complete and tested
- [ ] All blueprints pass functional parity tests
- [ ] Framework overhead measured for each language
- [ ] Documentation and examples complete

## Framework Selection Rationale

| Language | Framework | Why |
|----------|-----------|-----|
| Python | FastAPI | Modern, async, type-hints, popular |
| TypeScript | Express | De facto standard, minimal overhead |
| Go | Gin | Fast, idiomatic, minimalist |
| Java | Spring Boot | Enterprise standard, widely used |
| PHP | Laravel | Modern, developer-friendly, batteries-included |

## TDD Cycles (Per Framework)

Each framework follows identical TDD pattern. Example shown for FastAPI; repeat for others.

### Cycle 1: Basic HTTP Proxy

**RED**: Framework forwards requests to fraiseql-server
```python
# frameworks/fraiseql-python/fastapi/tests/test_proxy.py
from fastapi.testclient import TestClient
from app import app

def test_graphql_query_forwarding():
    """FastAPI forwards query to fraiseql-server."""
    client = TestClient(app)

    response = client.post(
        "/graphql",
        json={"query": "{ users { id name } }"}
    )

    assert response.status_code == 200
    assert "data" in response.json()

def test_mutation_forwarding():
    """FastAPI forwards mutations."""
    client = TestClient(app)

    response = client.post(
        "/graphql",
        json={
            "query": 'mutation { createUser(name: "Test", email: "test@example.com") { id } }'
        }
    )

    assert response.status_code == 200
    assert "data" in response.json()

def test_error_forwarding():
    """Errors from fraiseql-server are forwarded."""
    client = TestClient(app)

    response = client.post(
        "/graphql",
        json={"query": "{ invalidField }"}
    )

    assert response.status_code == 200
    assert "errors" in response.json()
```

**GREEN**: Minimal proxy implementation
```python
# frameworks/fraiseql-python/fastapi/app.py
import os
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="FraiseQL FastAPI Blueprint")

FRAISEQL_SERVER_URL = os.getenv("FRAISEQL_SERVER_URL", "http://localhost:8000")

@app.post("/graphql")
async def graphql(request: dict):
    """Forward GraphQL requests to fraiseql-server."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FRAISEQL_SERVER_URL}/graphql",
            json=request,
            timeout=10.0
        )
        return JSONResponse(response.json(), status_code=response.status_code)

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
```

**REFACTOR**: Add error handling, request validation, logging

**CLEANUP**: Format code, add docstrings

---

### Cycle 2: Error Handling & Validation

**RED**: Proper error handling for network failures, invalid input
```python
def test_invalid_request_format():
    """Invalid requests are rejected."""
    client = TestClient(app)

    response = client.post("/graphql", json={"invalid": "format"})
    assert response.status_code == 400

def test_fraiseql_server_unreachable():
    """Handles fraiseql-server being unreachable."""
    # Mock FRAISEQL_SERVER_URL to unreachable address
    response = client.post("/graphql", json={"query": "{ users { id } }"})
    assert response.status_code == 503  # Service Unavailable
```

**GREEN**: Add validation and error handling
```python
from pydantic import BaseModel, Field
from typing import Optional, Any

class GraphQLRequest(BaseModel):
    query: str
    variables: Optional[dict] = None
    operationName: Optional[str] = None

@app.post("/graphql")
async def graphql(request: GraphQLRequest):
    """Forward GraphQL requests with validation."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FRAISEQL_SERVER_URL}/graphql",
                json=request.dict(exclude_none=True),
                timeout=10.0
            )
            return JSONResponse(response.json(), status_code=response.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            {"errors": [{"message": "FraiseQL server unavailable"}]},
            status_code=503
        )
    except Exception as e:
        return JSONResponse(
            {"errors": [{"message": str(e)}]},
            status_code=500
        )
```

**REFACTOR**: Improve error messages, add request logging

**CLEANUP**: Verify all error paths tested

---

### Cycle 3: Performance & Observability

**RED**: Framework collects and exposes metrics
```python
def test_metrics_endpoint():
    """Metrics endpoint available."""
    response = client.get("/metrics")
    assert response.status_code == 200

def test_latency_tracking():
    """Request latency is tracked."""
    client.post("/graphql", json={"query": "{ users { id } }"})

    metrics = client.get("/metrics").text
    assert "graphql_request_duration_ms" in metrics
```

**GREEN**: Add metrics collection
```python
import time
from prometheus_client import Counter, Histogram, generate_latest

graphql_requests = Counter(
    "graphql_requests_total",
    "Total GraphQL requests",
    ["operation_type", "status"]
)

graphql_duration = Histogram(
    "graphql_request_duration_ms",
    "GraphQL request duration in ms"
)

@app.post("/graphql")
async def graphql(request: GraphQLRequest):
    """Forward with metrics."""
    start = time.time()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FRAISEQL_SERVER_URL}/graphql",
                json=request.dict(exclude_none=True),
                timeout=10.0
            )

        operation_type = "query" if "query" in request.query else "mutation"
        graphql_requests.labels(
            operation_type=operation_type,
            status="success"
        ).inc()

        return JSONResponse(response.json(), status_code=response.status_code)
    except Exception as e:
        graphql_requests.labels(
            operation_type="unknown",
            status="error"
        ).inc()
        raise
    finally:
        elapsed_ms = (time.time() - start) * 1000
        graphql_duration.observe(elapsed_ms)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()
```

**REFACTOR**: Add structured logging, trace IDs

**CLEANUP**: Test metrics accuracy

---

### Cycle 4: Documentation & Examples

**RED**: Blueprint includes clear documentation
```
framework_blueprint/
├── README.md              # Getting started
├── ARCHITECTURE.md        # Design decisions
├── API.md                 # Available endpoints
└── examples/
    ├── simple_query.py    # Example usage
    ├── mutation.py
    └── with_auth.py       # Future: auth integration
```

**GREEN**: Create comprehensive documentation
```markdown
# FastAPI FraiseQL Blueprint

## Overview

Minimal FastAPI implementation serving as a blueprint for integrating FraiseQL.

## Architecture

```
Client → FastAPI (validation, metrics, auth)
              ↓ HTTP
        fraiseql-server (query execution)
              ↓
        PostgreSQL
```

## Getting Started

```bash
# Start fraiseql-server
export DATABASE_URL="postgresql://..."
export FRAISEQL_SCHEMA_PATH="schema.compiled.json"
fraiseql-server

# Start FastAPI proxy
export FRAISEQL_SERVER_URL="http://localhost:8000"
uvicorn app:app --reload --port 8001
```

## API Endpoints

### POST /graphql
Execute GraphQL queries and mutations.

**Request:**
```json
{"query": "{ users { id name } }"}
```

**Response:**
```json
{"data": {"users": [...]}}
```

## Metrics

Prometheus metrics available at `/metrics`:
- `graphql_requests_total`: Request count by operation type and status
- `graphql_request_duration_ms`: Request latency histogram
```

**REFACTOR**: Add more examples, troubleshooting

**CLEANUP**: Ensure all documentation is current

---

## Framework Implementation Checklist

Each of 5 frameworks must have:

```
✅ HTTP proxy to fraiseql-server
✅ Request validation (JSON schema or equivalent)
✅ Error handling (network, timeout, validation)
✅ Metrics collection (latency, throughput, errors)
✅ Structured logging
✅ Health check endpoint
✅ Comprehensive tests
✅ README with examples
✅ Performance characteristics documented
✅ Language idioms followed
```

## Framework-Specific Notes

### Python (FastAPI)
- Use async/await for optimal performance
- Pydantic for request validation
- Prometheus for metrics
- Structlog for structured logging

### TypeScript (Express)
- Middleware-based architecture
- Express validators for request validation
- Prom-client for metrics
- Winston for logging

### Go (Gin)
- Gin middleware pattern
- Struct-based request parsing
- Prometheus Go client
- Zap logger

### Java (Spring Boot)
- Spring WebFlux for async
- Spring Validation
- Micrometer for metrics
- SLF4J/Logback for logging

### PHP (Laravel)
- Laravel middleware pipeline
- Laravel form requests
- Prometheus exporter
- Laravel logging

## Deliverables (Per Framework)

```
frameworks/fraiseql-[language]/[framework]/
├── src/app.[ext]           # Main application
├── tests/
│   ├── test_proxy.py
│   ├── test_errors.py
│   └── test_metrics.py
├── examples/
│   ├── simple_query.py
│   ├── mutation.py
│   └── with_filters.py
├── README.md
├── pyproject.toml|package.json|go.mod|pom.xml|composer.json
└── Dockerfile (optional)
```

## Parallel Execution

Phases 3 can be executed in parallel for all 5 languages:
- Python FastAPI
- TypeScript Express
- Go Gin
- Java Spring Boot
- PHP Laravel

Each language team works independently following the same TDD pattern.

## Dependencies

- Requires: Phase 2 (fraiseql-server running with baseline metrics)
- Blocks: Phase 4 (framework overhead measurement)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- Focus on simplicity: minimal proxy logic
- Each framework prioritizes language idioms
- Performance is measured in Phase 4
- Advanced features (auth, caching) can be added in Phase 5
- Examples demonstrate typical usage patterns
