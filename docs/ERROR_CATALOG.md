# Error Catalog & Solutions

## Overview

Complete reference of errors agents will encounter in VelocityBench, their root causes, and how to resolve them.

---

## Database Errors

### Connection Errors

#### `"Couldn't connect to server"`
**Root Cause**: PostgreSQL not running or connection credentials incorrect

**Symptoms**:
```
Error: could not connect to server: Connection refused
  Is the server running on host "localhost" (127.0.0.1) and accepting
  TCP/IP connections on port 5432?
```

**Solutions**:
1. **Check if PostgreSQL is running**:
   ```bash
   docker ps | grep postgres
   ```
   If not running:
   ```bash
   docker-compose up -d postgres
   ```

2. **Check connection credentials** in `.env`:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=velocitybench_test
   DB_USER=benchmark
   DB_PASSWORD=benchmark123
   ```

3. **Wait for database to start** (takes 10-15 seconds):
   ```bash
   sleep 15 && pytest tests/
   ```

**Prevention**: Use `.env.example` as template, ensure Docker is running

---

#### `"Role 'benchmark' does not exist"`
**Root Cause**: Database user not created

**Solution**:
```bash
docker-compose down postgres
docker-compose up -d postgres
docker exec postgres psql -U postgres -c "CREATE USER benchmark WITH PASSWORD 'benchmark123';"
docker exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE velocitybench_test TO benchmark;"
```

---

### Schema Errors

#### `"Column 'fk_author' doesn't exist"`
**Root Cause**: Using wrong identifier (UUID id instead of SERIAL pk_user)

**Example (WRONG)**:
```python
# ❌ Using UUID id as foreign key
cursor.execute("INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
               (user['id'], "Title"))  # uuid_obj not int!
```

**Example (CORRECT)**:
```python
# ✅ Using SERIAL pk_user as foreign key
cursor.execute("INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
               (user['pk_user'], "Title"))  # int!
```

**Solution**: Always use `pk_user` for foreign keys, `id` only for API queries

**Related**: See `docs/DATABASE_SCHEMA.md` - Trinity Pattern section

---

#### `"Duplicate key value violates unique constraint 'tb_user_username_key'"`
**Root Cause**: Username already exists

**Symptoms**:
```
psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "tb_user_username_key"
DETAIL:  Key (username)=(alice) already exists.
```

**Solutions**:
1. **Use unique username in test**:
   ```python
   def test_create_user(db, factory):
       user = factory.create_user(f"alice_{random_suffix}", "alice@example.com")
   ```

2. **Clear database between tests** (should be automatic):
   ```python
   def test_reset(db):
       # Transaction rollback happens automatically
       # Test is isolated from other tests
       pass
   ```

3. **Check test isolation**:
   - Ensure using `db` fixture (provides transaction isolation)
   - Run single test vs test suite to isolate issue

---

### Data Type Errors

#### `"Invalid input syntax for type uuid"`
**Root Cause**: Passing string UUID without conversion or wrong format

**Example (WRONG)**:
```python
cursor.execute("SELECT * FROM tb_user WHERE id = %s",
               ("550e8400-e29b-41d4-a716-446655440000",))  # String!
```

**Example (CORRECT)**:
```python
from uuid import UUID
user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
cursor.execute("SELECT * FROM tb_user WHERE id = %s", (user_id,))
```

**Solution**: Use Python `UUID` type for database UUIDs, strings for API payloads only

---

#### `"Integer out of range"`
**Root Cause**: SERIAL primary key value exceeds 2^31-1

**Symptom**: Inserting too many test records

**Solution**:
- SERIAL goes to 2,147,483,647 - very unlikely in testing
- If encountered, reset sequence:
  ```sql
  ALTER SEQUENCE tb_user_pk_user_seq RESTART WITH 1;
  ```

---

## REST API Errors

### Request Errors

#### `400 Bad Request - "Invalid email format"`
**Root Cause**: Email validation failed

**Example (WRONG)**:
```python
response = client.post("/users", json={
    "username": "alice",
    "email": "not-an-email"  # ❌ No @ sign
})
```

**Example (CORRECT)**:
```python
response = client.post("/users", json={
    "username": "alice",
    "email": "alice@example.com"
})
```

**Solution**: Follow standard email format: `user@domain.com`

**Related**: See `docs/API_SCHEMAS.md` - Validation Rules

---

#### `400 Bad Request - "Field required"`
**Root Cause**: Missing required field in request

**Example (WRONG)**:
```python
response = client.post("/users", json={
    "username": "alice"
    # ❌ Missing 'email'
})
```

**Example (CORRECT)**:
```python
response = client.post("/users", json={
    "username": "alice",
    "email": "alice@example.com"
})
```

**Solution**: Check `docs/API_SCHEMAS.md` for required vs optional fields

---

#### `422 Unprocessable Entity - "String should have at most 100 characters"`
**Root Cause**: Field exceeds maximum length

**Example (WRONG)**:
```python
response = client.post("/users", json={
    "username": "a" * 500  # ❌ Exceeds 100 char limit
})
```

**Example (CORRECT)**:
```python
response = client.post("/users", json={
    "username": "alice"  # ✅ 5 characters
})
```

**Solution**: Reference field constraints in `docs/DATABASE_SCHEMA.md`

---

### Response Errors

#### `404 Not Found`
**Root Cause**: Resource with that ID doesn't exist

**Example (WRONG)**:
```python
response = client.get("/users/00000000-0000-0000-0000-000000000000")
# 404 - UUID doesn't exist
```

**Solution**:
1. Verify resource was created:
   ```python
   user = factory.create_user("alice", "alice@example.com")
   response = client.get(f"/users/{user['id']}")
   assert response.status_code == 200
   ```

2. Check database directly:
   ```python
   cursor.execute("SELECT id FROM tb_user WHERE username = %s", ("alice",))
   result = cursor.fetchone()
   ```

---

#### `409 Conflict - "Username already exists"`
**Root Cause**: Duplicate unique field

**Solution**: Same as database duplicate key error above

---

### Header/Format Errors

#### `415 Unsupported Media Type`
**Root Cause**: Missing or wrong `Content-Type` header

**Example (WRONG)**:
```python
response = client.post("/users", data='{"username":"alice"}')  # Wrong type!
```

**Example (CORRECT)**:
```python
response = client.post("/users",
                      json={"username": "alice"},  # ✅ json= handles headers
                      headers={"Content-Type": "application/json"})
```

**Solution**: Use `json=` parameter in requests library, not `data=` string

---

## GraphQL Errors

### Query Errors

#### `"Field 'nonexistent' doesn't exist on type 'User'"`
**Root Cause**: Querying non-existent field

**Example (WRONG)**:
```graphql
query {
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    firstName       # ❌ Field doesn't exist (is 'first_name')
  }
}
```

**Example (CORRECT)**:
```graphql
query {
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    firstName       # ✅ Correct camelCase
  }
}
```

**Note**: GraphQL uses `camelCase`, database uses `snake_case`. Frameworks handle conversion.

**Solution**: Reference `docs/API_SCHEMAS.md` for correct field names

---

#### `"Expected 1 arguments but got 2"`
**Root Cause**: Wrong number of arguments to query/mutation

**Example (WRONG)**:
```graphql
mutation {
  createUser(username: "alice", email: "alice@example.com") {  # ❌ Wrong args
    id
    username
  }
}
```

**Example (CORRECT)**:
```graphql
mutation {
  createUser(input: {
    username: "alice"
    email: "alice@example.com"
  }) {
    id
    username
  }
}
```

**Solution**: Check schema in `docs/API_SCHEMAS.md` for argument structure

---

#### `"Argument 'id' of type 'ID!' is required and was not provided"`
**Root Cause**: Required argument missing

**Example (WRONG)**:
```graphql
query {
  user {  # ❌ Missing required 'id' argument
    username
  }
}
```

**Example (CORRECT)**:
```graphql
query {
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    username
  }
}
```

---

### Mutation Errors

#### `"Variable '$input' of type 'CreateUserInput!' was not provided"`
**Root Cause**: Missing variable in GraphQL request

**Example (WRONG)**:
```json
{
  "query": "mutation CreateUser($input: CreateUserInput!) { createUser(input: $input) { id } }"
  // ❌ Missing 'variables' key
}
```

**Example (CORRECT)**:
```json
{
  "query": "mutation CreateUser($input: CreateUserInput!) { createUser(input: $input) { id } }",
  "variables": {
    "input": {
      "username": "alice",
      "email": "alice@example.com"
    }
  }
}
```

---

## Test Errors

### Isolation Issues

#### `"Test passed alone but failed in suite"`
**Root Cause**: Test isolation failure (data from other tests bleeding through)

**Symptom**:
```bash
pytest tests/test_users.py::test_create_user  # ✅ Passes
pytest tests/test_users.py                   # ❌ Fails
```

**Solution**:
1. **Ensure using `db` fixture**:
   ```python
   def test_something(db, factory):  # ✅ Uses shared db fixture
       user = factory.create_user("alice", "alice@example.com")
   ```

2. **Verify transaction isolation is working**:
   ```bash
   pytest tests/test_users.py -vv --tb=short
   ```

3. **Check for manual transactions**:
   ```python
   # ❌ Bad: Manual transaction handling
   cursor = db.cursor()
   cursor.execute("BEGIN")  # Don't do this!

   # ✅ Good: db fixture handles transactions
   cursor = db.cursor()
   # Transaction managed by fixture
   ```

**Related**: See `docs/TEST_ISOLATION_STRATEGY.md`

---

#### `"RuntimeError: Event loop is closed"`
**Root Cause**: AsyncDatabase connection not properly cleaned up

**Solution**:
1. **Use AsyncDatabase fixture properly**:
   ```python
   # ❌ Wrong: Direct instantiation
   db = AsyncDatabase()
   await db.connect(...)

   # ✅ Right: Use fixture
   async def test_something(async_db):
       result = await async_db.fetch_one("SELECT 1")
   ```

2. **Ensure pytest-asyncio is installed**:
   ```bash
   pip install pytest-asyncio
   ```

3. **Mark async tests properly**:
   ```python
   import pytest

   @pytest.mark.asyncio
   async def test_async_operation(async_db):
       pass
   ```

---

### Fixture Errors

#### `"Fixture 'db' not found"`
**Root Cause**: Missing `conftest.py` or wrong import

**Solution**:
1. **Verify conftest.py exists**:
   ```bash
   ls tests/common/conftest.py
   ```

2. **Ensure conftest.py imports correctly**:
   ```python
   # tests/common/conftest.py
   from tests.common.fixtures import db, factory, bulk_factory
   ```

3. **Verify test finds conftest.py**:
   ```bash
   pytest tests/ -vv  # Ensure pytest discovery works
   ```

---

#### `"TypeError: fixture 'factory' has no params"`
**Root Cause**: Factory method called incorrectly

**Example (WRONG)**:
```python
def test_create_user(factory):
    user = factory.create_user()  # ❌ Missing required args
```

**Example (CORRECT)**:
```python
def test_create_user(factory):
    user = factory.create_user("alice", "alice@example.com")
```

**Solution**: Check `docs/FIXTURE_FACTORY_GUIDE.md` for method signatures

---

## Framework-Specific Errors

### FastAPI/Starlette

#### `"Starlette received an ASGI message of type 'lifespan.startup' that it does not handle"`
**Root Cause**: Missing lifespan event handlers

**Solution**: Ensure `main.py` has `@asynccontextmanager` for startup/shutdown

---

#### `"No module named 'pydantic'"`
**Root Cause**: Dependencies not installed

**Solution**:
```bash
cd frameworks/fastapi-rest
pip install -r requirements.txt
```

---

### Strawberry GraphQL

#### `"TypeError: 'NoneType' object is not callable"`
**Root Cause**: Resolver returning None instead of expected type

**Example (WRONG)**:
```python
@strawberry.field
async def users(self) -> list[User]:
    return None  # ❌ Should return list
```

**Example (CORRECT)**:
```python
@strawberry.field
async def users(self) -> list[User]:
    rows = await db.fetch_all("SELECT * FROM tb_user")
    return [User(**row) for row in rows]
```

---

### Express/Node.js

#### `"Cannot find module 'express'"`
**Root Cause**: Dependencies not installed

**Solution**:
```bash
cd frameworks/express-rest
npm install
```

---

#### `"Error: listen EADDRINUSE: address already in use :::8000"`
**Root Cause**: Port already in use

**Solution**:
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
PORT=8001 npm start
```

---

## Common Anti-Patterns

### ❌ Don't: Mix Identifiers
```python
# WRONG: Using UUID for FK
cursor.execute("INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
               (UUID("550e8400-e29b-41d4-a716-446655440000"), "Title"))
```

### ✅ Do: Use Correct Identifier Types
```python
# CORRECT: Using SERIAL int for FK
cursor.execute("INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
               (user['pk_user'], "Title"))
```

---

### ❌ Don't: Ignore Transaction Isolation
```python
# WRONG: Bypassing db fixture
import psycopg
conn = psycopg.connect("...")
cursor = conn.cursor()
```

### ✅ Do: Use Fixture for Isolation
```python
# CORRECT: Using db fixture
def test_something(db, factory):
    user = factory.create_user("alice", "alice@example.com")
    # Transaction isolation handled automatically
```

---

### ❌ Don't: Use Hardcoded IDs
```python
# WRONG: Hardcoded UUID
response = client.get("/users/550e8400-e29b-41d4-a716-446655440000")
```

### ✅ Do: Create and Use Dynamic IDs
```python
# CORRECT: Create user and use returned ID
user = factory.create_user("alice", "alice@example.com")
response = client.get(f"/users/{user['id']}")
```

---

## Performance Issues

### N+1 Query Problem

**Symptom**: Slow when retrieving many related records

**Example (WRONG)**:
```python
# ❌ N+1: One query per item
posts = db.fetch_all("SELECT * FROM tb_post LIMIT 100")
for post in posts:
    author = db.fetch_one("SELECT * FROM tb_user WHERE pk_user = %s",
                          (post['fk_author'],))  # 100 queries!
```

**Example (CORRECT)**:
```python
# ✅ Single query with join
posts = db.fetch_all("""
    SELECT p.*, u.username
    FROM tb_post p
    JOIN tb_user u ON p.fk_author = u.pk_user
    LIMIT 100
""")
```

**Solution**: Use JOINs instead of separate queries; see `docs/CODEBASE_NAVIGATION.md` - Query Patterns

---

### Missing Indexes

**Symptom**: Query is slow on large dataset

**Example (PROBLEM)**:
```sql
SELECT * FROM tb_post WHERE status = 'published' ORDER BY published_at DESC
-- Slow without index on (status, published_at)
```

**Solution**: Check `docs/DATABASE_SCHEMA.md` for recommended indexes

---

## Debugging Strategy

### For Agents:

1. **Identify error type**: Database, API, test, or framework?
2. **Search catalog**: Find matching error above
3. **Check root cause**: Understand what went wrong
4. **Apply solution**: Follow provided fix
5. **Verify fix**: Run test/query again
6. **Reference docs**: Link to relevant detailed documentation

### Common Debugging Commands:

```bash
# See database state
docker exec postgres psql -U benchmark -d velocitybench_test -c "SELECT * FROM tb_user;"

# Test API manually
curl -X GET "http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000"

# Run test with verbose output
pytest tests/test_users.py::test_create_user -vv

# Check logs
docker logs postgres
docker logs velocitybench-fastapi-1

# Verify connections
docker ps
```

---

## Related Documentation

- **Database Schema**: `docs/DATABASE_SCHEMA.md` - Constraints and validation rules
- **API Schemas**: `docs/API_SCHEMAS.md` - Field requirements and formats
- **Testing**: `docs/TESTING_README.md` - Test execution and debugging
- **Development**: `docs/DEVELOPMENT.md` - Environment setup

