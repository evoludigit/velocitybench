# Cross-Framework Test Data Consistency

## Overview

VelocityBench implements multiple frameworks (FastAPI, Flask, Strawberry, Graphene, Ariadne, ASGI-GraphQL) all working against the same PostgreSQL database with identical schema. This guide ensures test data is consistent across all framework implementations.

---

## Shared Database Schema

All frameworks use the **Trinity Pattern** schema in the `benchmark` schema:

```sql
CREATE SCHEMA benchmark;

CREATE TABLE benchmark.tb_user (
    pk_user SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() UNIQUE,
    username VARCHAR(255) UNIQUE NOT NULL,
    identifier VARCHAR(255),
    email VARCHAR(255),
    full_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE benchmark.tb_post (
    pk_post SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() UNIQUE,
    fk_author INT NOT NULL REFERENCES benchmark.tb_user(pk_user),
    title VARCHAR(255) NOT NULL,
    identifier VARCHAR(255),
    content TEXT,
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE benchmark.tb_comment (
    pk_comment SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() UNIQUE,
    fk_post INT NOT NULL REFERENCES benchmark.tb_post(pk_post),
    fk_author INT NOT NULL REFERENCES benchmark.tb_user(pk_user),
    content TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Test Data Factory

The shared `tests/common/fixtures.py` provides consistent test data creation:

```python
# All frameworks use this same factory
from tests.common.fixtures import db, factory

def test_across_all_frameworks(db, factory):
    """Test data is created identically across frameworks."""
    # All frameworks use identical factory
    user = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=user["pk_user"], title="Post")

    # Same data structure for all frameworks
    assert user["username"] == "alice"
    assert post["fk_author"] == user["pk_user"]
```

---

## Data Consistency Principles

### 1. **Schema Identity**

All frameworks share identical schema:

| Framework | Tables | Fields | Constraints |
|-----------|--------|--------|-------------|
| FastAPI | tb_user, tb_post, tb_comment | Same | Same |
| Flask | tb_user, tb_post, tb_comment | Same | Same |
| Strawberry | tb_user, tb_post, tb_comment | Same | Same |
| Graphene | tb_user, tb_post, tb_comment | Same | Same |
| Ariadne | tb_user, tb_post, tb_comment | Same | Same |
| ASGI-GraphQL | tb_user, tb_post, tb_comment | Same | Same |

### 2. **Data Types**

Framework-specific differences must map consistently:

```
Database Type         →  GraphQL Type        →  REST API Type
uuid (tb_user.id)    →  String!             →  string (UUID)
int (pk_user)        →  Int!                →  integer
varchar (username)   →  String!             →  string
timestamp (created)  →  String! (ISO 8601)  →  string (datetime)
```

### 3. **Identifier Strategy**

Trinity Pattern uses three identifiers:

```python
# All frameworks use these identifiers
user = {
    "pk_user": 1,                    # Internal: primary key (int)
    "id": UUID("..."),               # Public API: UUID
    "username": "alice",             # Human-readable: unique string
    "identifier": "alice-smith",     # URL-friendly: slug
}

# Framework implementations differ but must map consistently:
# GraphQL: query by `id` (UUID) or `username` (string)
# REST: query by `id` (UUID) or `username` (string)
# Query: queryUser(id: "550e8400-e29b-41d4-a716-446655440000")
```

---

## Cross-Framework Test Data Examples

### Example 1: User Creation

**FastAPI (REST):**
```python
def test_user_creation_fastapi(client, factory):
    """Create user via FastAPI REST."""
    user = factory.create_user("alice", "alice@example.com")

    response = client.get(f"/users/{user['id']}")
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
```

**Strawberry (GraphQL):**
```python
def test_user_creation_strawberry(client, factory):
    """Create user queried via Strawberry GraphQL."""
    user = factory.create_user("alice", "alice@example.com")

    query = """
    query { user(id: "%s") { username email } }
    """ % user["id"]

    response = client.post("/graphql", json={"query": query})
    assert response.json()["data"]["user"]["username"] == "alice"
```

**Both frameworks use same test data creation!**

### Example 2: Post with Author

**FastAPI (REST):**
```python
def test_post_with_author_fastapi(client, factory):
    """Test post includes author information."""
    user = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=user["pk_user"], title="Post")

    response = client.get(f"/posts/{post['id']}")
    assert response.json()["author"]["username"] == "alice"
```

**Strawberry (GraphQL):**
```python
def test_post_with_author_strawberry(client, factory):
    """Test post includes author information."""
    user = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=user["pk_user"], title="Post")

    query = """
    query { post(id: "%s") { title author { username } } }
    """ % post["id"]

    response = client.post("/graphql", json={"query": query})
    assert response.json()["data"]["post"]["author"]["username"] == "alice"
```

**Same test data, different API interfaces!**

---

## Ensuring Consistency

### 1. **Use Shared Fixtures**

✅ **DO:**
```python
# All frameworks import same fixtures
from tests.common.fixtures import db, factory

def test_anything(db, factory):
    """Uses shared fixture - consistent across frameworks."""
    user = factory.create_user("alice", "alice@example.com")
    # This is identical in FastAPI, Flask, Strawberry, etc.
```

❌ **DON'T:**
```python
# Custom database connections - consistency risk
def test_anything():
    """Custom connection - might differ from other frameworks."""
    conn = psycopg.connect(...)  # Manual connection
    # Might use different isolation level, settings, etc.
```

### 2. **Validate Data After Creation**

```python
def test_post_factory_creates_correct_data_across_frameworks(db, factory):
    """Verify factory creates data correctly."""
    user = factory.create_user("alice", "alice@example.com", full_name="Alice Smith")
    post = factory.create_post(fk_author=user["pk_user"], title="My Post", content="Content here")

    # Verify database state directly
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM benchmark.tb_user WHERE pk_user = %s", (user["pk_user"],))
        db_user = cursor.fetchone()
        assert db_user["username"] == "alice"
        assert db_user["full_name"] == "Alice Smith"

        cursor.execute("SELECT * FROM benchmark.tb_post WHERE pk_post = %s", (post["pk_post"],))
        db_post = cursor.fetchone()
        assert db_post["title"] == "My Post"
        assert db_post["content"] == "Content here"
```

### 3. **Test Both Directions**

Test that data flows both ways correctly:

```python
def test_create_and_read_consistency_fastapi(client, factory):
    """Test create (factory) and read (API) are consistent."""
    # Create via factory (what all tests use)
    user = factory.create_user("alice", "alice@example.com")

    # Read via API
    response = client.get(f"/users/{user['id']}")

    # Verify consistency
    api_user = response.json()
    assert api_user["username"] == user["username"]
    assert api_user["email"] == user["email"]
    assert api_user["id"] == str(user["id"])  # UUID serialization

def test_create_and_read_consistency_strawberry(client, factory):
    """Test create (factory) and read (GraphQL) are consistent."""
    # Create via factory (what all tests use)
    user = factory.create_user("alice", "alice@example.com")

    # Read via GraphQL
    query = 'query { user(id: "%s") { username email id } }' % user["id"]
    response = client.post("/graphql", json={"query": query})

    # Verify consistency
    gql_user = response.json()["data"]["user"]
    assert gql_user["username"] == user["username"]
    assert gql_user["email"] == user["email"]
    assert gql_user["id"] == str(user["id"])  # UUID serialization
```

---

## Framework-Specific Considerations

### UUID Serialization

Different frameworks may serialize UUIDs differently:

```python
# FastAPI returns UUID string
"id": "550e8400-e29b-41d4-a716-446655440000"

# GraphQL returns UUID string
"id": "550e8400-e29b-41d4-a716-446655440000"

# Database stores as uuid type
id = UUID("550e8400-e29b-41d4-a716-446655440000")

# Always compare as strings to avoid type issues
assert str(user["id"]) == api_user["id"]
```

### Timestamp Formats

Different frameworks may return timestamps in different formats:

```python
# Database: TIMESTAMP
created_at = datetime(2025, 1, 31, 10, 0, 0)

# FastAPI: ISO 8601 string
"created_at": "2025-01-31T10:00:00Z"

# GraphQL: ISO 8601 string
"created_at": "2025-01-31T10:00:00Z"

# Compare by parsing
from datetime import datetime
api_timestamp = datetime.fromisoformat(response["created_at"])
assert api_timestamp.date() == datetime.now().date()
```

### Null Handling

Be consistent with null/None values:

```python
# All frameworks should handle these identically:
user = factory.create_user("alice", "alice@example.com")
# bio is not provided - should be None/null

# FastAPI
response = client.get(f"/users/{user['id']}")
assert response.json()["bio"] is None

# GraphQL
query = 'query { user(id: "%s") { bio } }' % user["id"]
response = client.post("/graphql", json={"query": query})
assert response.json()["data"]["user"]["bio"] is None
```

---

## Multi-Framework Test Examples

### Running Same Test Against All Frameworks

```python
import pytest

FRAMEWORKS = ["fastapi", "flask", "strawberry", "graphene"]

@pytest.fixture(params=FRAMEWORKS)
def any_framework_client(request):
    """Provide a client for any framework."""
    framework = request.param
    # Import correct client based on framework
    if framework == "fastapi":
        from frameworks.fastapi_rest.tests import client as fc
        return fc, framework
    elif framework == "strawberry":
        from frameworks.strawberry.tests import client as sc
        return sc, framework
    # ... etc

def test_user_query_works_on_all_frameworks(any_framework_client, factory):
    """Same test runs on all frameworks."""
    client, framework = any_framework_client

    # Create data (identical across frameworks)
    user = factory.create_user("alice", "alice@example.com")

    # Query via framework-specific API
    if framework in ["fastapi", "flask"]:
        response = client.get(f"/users/{user['id']}")
        assert response.json()["username"] == "alice"
    else:  # GraphQL frameworks
        query = f'query {{ user(id: "{user["id"]}") {{ username }} }}'
        response = client.post("/graphql", json={"query": query})
        assert response.json()["data"]["user"]["username"] == "alice"
```

### Comparing Framework Responses

```python
def test_user_response_structure_consistent(factory):
    """Verify all frameworks return same user fields."""
    user = factory.create_user("alice", "alice@example.com", full_name="Alice Smith")

    # Test REST framework (FastAPI)
    from frameworks.fastapi_rest.tests import client as fastapi_client
    rest_response = fastapi_client.get(f"/users/{user['id']}").json()

    # Test GraphQL framework (Strawberry)
    from frameworks.strawberry.tests import client as graphql_client
    gql_query = f'query {{ user(id: "{user["id"]}") {{ username fullName }} }}'
    gql_response = graphql_client.post(
        "/graphql", json={"query": gql_query}
    ).json()["data"]["user"]

    # Verify both return same data
    assert rest_response["username"] == gql_response["username"]
    assert rest_response["full_name"] == gql_response["fullName"]
```

---

## Data Consistency Checklist

Before adding framework tests:

- [ ] Uses `tests/common/fixtures.db` for database connection
- [ ] Uses `tests/common/fixtures.factory` for data creation
- [ ] Tests verify data created by factory matches database
- [ ] UUID serialization handled correctly
- [ ] Timestamp formats match expectations
- [ ] Null/None values handled consistently
- [ ] Test passes on multiple consecutive runs (no race conditions)
- [ ] Test data is isolated (no cross-test pollution)

---

## Troubleshooting Consistency Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Data missing in one framework | Factory not used | Use `factory` fixture for all frameworks |
| UUID mismatch | Serialization difference | Compare as strings: `str(uuid)` |
| Timestamp mismatch | Timezone difference | Parse ISO 8601 and compare dates |
| Foreign key error | Missing parent | Create parent before child (use factory) |
| Test passes alone, fails in suite | Test isolation issue | Verify using `db` fixture with transaction |

---

## Related Documentation

- [Test Isolation Strategy](TEST_ISOLATION_STRATEGY.md) - How data is isolated
- [Fixture Factory Guide](FIXTURE_FACTORY_GUIDE.md) - How to create test data
- [Test Naming Conventions](TEST_NAMING_CONVENTIONS.md) - How to name tests
