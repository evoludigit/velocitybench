# Phase 2: Python Framework Adaptation

## Objective

Adapt existing Python framework implementations (FastAPI, Flask, Strawberry, Graphene) to use the FraiseQL-compiled schema, replacing manual resolver logic with FraiseQL's deterministic execution engine.

## Success Criteria

- [ ] FastAPI-REST adapted: Uses FraiseQL runtime, tests passing
- [ ] Flask-REST adapted: Uses FraiseQL runtime, tests passing
- [ ] Strawberry adapted: Uses FraiseQL runtime, tests passing
- [ ] Graphene adapted: Uses FraiseQL runtime, tests passing
- [ ] All common test suites pass across all frameworks
- [ ] No resolver/hook-based query logic remains
- [ ] Performance benchmarks established
- [ ] Documentation updated

## TDD Cycles

### Cycle 1: FastAPI-REST Adaptation

**RED**: Write test verifying FastAPI serves FraiseQL schema
```python
# tests/fastapi_rest/test_fraiseql_integration.py
def test_fastapi_loads_fraiseql_schema():
    from frameworks.fraiseql_python.fastapi_rest.app import app
    assert app.fraiseql_schema is not None
    assert "users" in app.fraiseql_schema.queries

def test_fastapi_query_uses_fraiseql_execution():
    client = TestClient(app)
    response = client.post(
        "/graphql",
        json={"query": "{ users { id name } }"}
    )
    assert response.status_code == 200
    # Verify query executed via FraiseQL, not custom resolver
    assert response.json()["data"]["users"] is not None
```

**GREEN**: Minimal FastAPI + FraiseQL integration
```python
# frameworks/fraiseql_python/fastapi_rest/main.py
from fastapi import FastAPI
from fraiseql.runtime import FraiseQLRuntime
from strawberry.asgi import GraphQLTransport

app = FastAPI()
runtime = FraiseQLRuntime("schema.compiled.json")

@app.post("/graphql")
async def graphql_query(request: dict):
    result = await runtime.execute(request["query"])
    return {"data": result}
```

**REFACTOR**: Add proper GraphQL handling, error handling, auth middleware

**CLEANUP**: Remove old resolver logic, verify all endpoints work

---

### Cycle 2: Flask-REST Adaptation

**RED**: Test Flask serves FraiseQL queries correctly
```python
def test_flask_uses_fraiseql():
    from frameworks.fraiseql_python.flask_rest.app import app
    with app.test_client() as client:
        response = client.post(
            "/graphql",
            json={"query": "{ users { id } }"}
        )
        assert response.status_code == 200
```

**GREEN**: Minimal Flask + FraiseQL
```python
# frameworks/fraiseql_python/flask_rest/app.py
from flask import Flask, request, jsonify
from fraiseql.runtime import FraiseQLRuntime

app = Flask(__name__)
runtime = FraiseQLRuntime("schema.compiled.json")

@app.route("/graphql", methods=["POST"])
def graphql():
    query = request.json.get("query")
    result = runtime.execute(query)
    return jsonify({"data": result})
```

**REFACTOR**: Add error handling, validation, middleware

**CLEANUP**: Remove Flask-specific resolvers

---

### Cycle 3: Strawberry Adaptation

**RED**: Test Strawberry uses FraiseQL backend
```python
def test_strawberry_uses_fraiseql():
    from frameworks.fraiseql_python.strawberry.schema import schema
    query = "{ users { id name } }"
    result = schema.execute_sync(query)
    assert result.data is not None
```

**GREEN**: Strawberry with FraiseQL data loader
```python
# frameworks/fraiseql_python/strawberry/schema.py
import strawberry
from fraiseql.runtime import FraiseQLRuntime

runtime = FraiseQLRuntime("schema.compiled.json")

@strawberry.type
class Query:
    @strawberry.field
    async def users(self) -> list[User]:
        return await runtime.resolve_query("users")
```

**REFACTOR**: Integrate with Strawberry's type system

**CLEANUP**: Ensure all resolvers delegate to FraiseQL

---

### Cycle 4: Graphene Adaptation

**RED**: Test Graphene uses FraiseQL
```python
def test_graphene_uses_fraiseql():
    from frameworks.fraiseql_python.graphene.schema import schema
    result = schema.execute("{ users { id } }")
    assert result.data is not None
```

**GREEN**: Graphene with FraiseQL backend
```python
# frameworks/fraiseql_python/graphene/schema.py
import graphene
from fraiseql.runtime import FraiseQLRuntime

runtime = FraiseQLRuntime("schema.compiled.json")

class Query(graphene.ObjectType):
    users = graphene.List(User)

    def resolve_users(self, info):
        return runtime.resolve_query("users")
```

**REFACTOR**: Integrate with Graphene's resolver pattern

**CLEANUP**: Verify all fields delegate to FraiseQL

---

### Cycle 5: Shared Test Suite Integration

**RED**: Common test suite runs against all 4 Python frameworks
```python
# tests/common/test_endpoints_base.py - Already exists
# Updated to be parameterized
import pytest

@pytest.mark.parametrize("framework", [
    "fastapi_rest",
    "flask_rest",
    "strawberry",
    "graphene"
])
def test_users_query_returns_all_users(framework):
    client = get_client(framework)
    response = client.query("{ users { id name email } }")
    assert len(response["data"]["users"]) > 0

def test_mutations_work_across_frameworks(framework):
    client = get_client(framework)
    response = client.mutate(
        """
        mutation {
            createUser(name: "Test", email: "test@example.com") {
                id name email
            }
        }
        """
    )
    assert response["data"]["createUser"]["id"]
```

**GREEN**: Create test factory that works with all frameworks
```python
# tests/common/factory.py
class FrameworkTestClient:
    def __init__(self, framework_name):
        if framework_name == "fastapi_rest":
            from frameworks.fraiseql_python.fastapi_rest.app import app
            self.client = TestClient(app)
        elif framework_name == "flask_rest":
            from frameworks.fraiseql_python.flask_rest.app import app
            self.client = app.test_client()
        # ... etc

    def query(self, query_string):
        response = self.client.post(
            "/graphql",
            json={"query": query_string}
        )
        return response.json()
```

**REFACTOR**: Add query builder, mutation support, validation

**CLEANUP**: Ensure all tests are idempotent and isolated

---

### Cycle 6: Performance & Parity Validation

**RED**: Verify all frameworks achieve equivalent performance
```python
def test_query_performance_parity():
    benchmarks = {}
    for framework in ["fastapi_rest", "flask_rest", "strawberry", "graphene"]:
        client = get_client(framework)
        start = time.time()
        for _ in range(100):
            client.query("{ users { id } }")
        benchmarks[framework] = time.time() - start

    # All should be within 10% of best
    best = min(benchmarks.values())
    for framework, time_taken in benchmarks.items():
        assert time_taken <= best * 1.1
```

**GREEN**: Run common test suite, collect performance metrics

**REFACTOR**: Optimize bottlenecks if found

**CLEANUP**: Document performance characteristics

---

## Directory Structure (Python)

```
frameworks/
└── fraiseql-python/
    ├── shared/
    │   ├── runtime.py              # FraiseQL runtime wrapper
    │   ├── client.py               # Shared test client
    │   ├── middleware.py           # Auth, logging, error handling
    │   └── types.py                # Generated types from schema
    │
    ├── fastapi-rest/
    │   ├── main.py                 # FastAPI app with FraiseQL
    │   ├── routes.py               # GraphQL endpoint
    │   ├── pyproject.toml
    │   └── tests/
    │
    ├── flask-rest/
    │   ├── app.py                  # Flask app
    │   ├── routes.py               # Blueprints
    │   └── tests/
    │
    ├── strawberry/
    │   ├── schema.py               # Strawberry schema
    │   ├── app.py                  # ASGI app
    │   └── tests/
    │
    └── graphene/
        ├── schema.py               # Graphene schema
        ├── app.py                  # ASGI/WSGI app
        └── tests/
```

## Migration Checklist

- [ ] FastAPI resolver logic → FraiseQL queries
- [ ] Flask resolver logic → FraiseQL queries
- [ ] Strawberry resolvers → FraiseQL backend
- [ ] Graphene resolvers → FraiseQL backend
- [ ] All custom ORM logic removed
- [ ] Error handling unified via FraiseQL
- [ ] Authorization moved to schema metadata
- [ ] Common tests parameterized and passing

## Database Alignment

**No schema changes required** - Database structure must already match Phase 1 schema.

## Dependencies

- Requires: Phase 1 (schema definition complete)
- Blocks: Phase 7 (cross-language testing)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- No resolver logic in frameworks - all query execution via FraiseQL
- Framework role shifts to: routing, auth, caching, observability
- Shared test suite validates behavior, not implementation
