# VelocityBench Testing Templates

Reusable test templates for implementing tests across all VelocityBench frameworks.

**Key Principle**: All frameworks test against a **single shared PostgreSQL database** running in Docker. No mocking - just real database testing.

## Overview

These templates provide a starting point for testing each framework. They include:

- ✅ **Shared PostgreSQL database** connection
- ✅ **Transaction isolation** for automatic cleanup
- ✅ **Test factory pattern** for creating test data
- ✅ **Real database tests** (not mocks)
- ✅ **Arrange-Act-Assert pattern**
- ✅ **Best practices** for each language

## Architecture

```
┌─────────────────────────────────┐
│   PostgreSQL Container (Docker)  │
│   velocitybench_test database   │
└─────────────────────────────────┘
         ↓ (shared)
┌────────┬──────────┬────────────┐
│ Python │ TypeScript  │   Go    │
│ Tests  │   Tests    │  Tests  │
└────────┴──────────┴────────────┘

Each test:
1. Starts transaction
2. Creates test data
3. Runs test
4. Rollback (automatic cleanup)
```

## Getting Started

### 1. Start the Shared Database

```bash
# From repository root
docker-compose up -d postgres

# Verify it's running
psql -h localhost -U velocitybench -d velocitybench_test -c "SELECT 1"
```

### 2. Copy Templates to Your Framework

```bash
# Python
cp testing-templates/conftest.py frameworks/{framework}/tests/
cp testing-templates/test_example.py frameworks/{framework}/tests/test_resolvers.py

# TypeScript (if needed)
cp testing-templates/test.example.ts frameworks/{framework}/tests/test.example.ts

# Go (if needed)
cp testing-templates/example_test.go frameworks/{framework}/
```

### 3. Update Database Connection

Edit the copied files and update:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (if different)
- Or use environment variables: `DB_HOST`, `DB_PORT`, etc.

### 4. Customize for Your Framework

- Add your resolver/handler imports
- Update factory methods for your models
- Add tests specific to your resolvers
- Follow the Arrange-Act-Assert pattern

### 5. Run Tests

```bash
cd frameworks/{framework}

# Python
pytest tests/ --cov=src

# TypeScript
npm test -- --coverage

# Go
go test -v -cover ./...

# Java
mvn test

# Rust
cargo test

# PHP
php artisan test

# Ruby
bundle exec rspec

# C#
dotnet test
```

## Files

### Python

**`conftest.py`** - pytest fixtures

Features:
- `db` fixture: Connection to shared PostgreSQL with transaction isolation
- `factory` fixture: TestFactory for creating test data
- Auto-cleanup via rollback

**`test_example.py`** - Complete test suite example

Includes:
- Query tests (list, by ID, nonexistent)
- Mutation tests (create, update, delete)
- Validation tests
- Relationship tests
- Edge case tests
- 80+ lines of documented examples

### TypeScript

**`test.example.ts`** - Jest test configuration and examples

Includes:
- Database connection setup
- Transaction wrapper for test isolation
- Factory methods
- Unit and integration test examples
- Error handling patterns

### Go

**`example_test.go`** - Go testing patterns

Includes:
- TestDB helper
- Transaction wrapper
- Test data models
- TestFactory pattern
- Example tests using testify

## Key Patterns

### Transaction Isolation (Automatic Cleanup)

Each test runs in a transaction that's automatically rolled back:

**Python**:
```python
@pytest.fixture
def db():
    conn = psycopg2.connect(...)
    conn.begin()  # Start transaction
    yield conn
    conn.rollback()  # Automatic cleanup
```

**TypeScript**:
```typescript
export const withTransaction = async (testFn) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await testFn();
    await client.query('ROLLBACK');
  } finally {
    client.release();
  }
};
```

**Go**:
```go
func withTransaction(t *testing.T, db *sql.DB, testFn func(*sql.Tx)) {
  tx, _ := db.Begin()
  defer tx.Rollback()  // Automatic cleanup
  testFn(tx)
}
```

### Test Factory Pattern

Create test data consistently:

**Python**:
```python
user = factory.create_user("Alice", "alice@example.com")
company = factory.create_company("ACME Corp")
product = factory.create_product("Widget", 19.99, company["id"])
```

**TypeScript**:
```typescript
const user = await factory.createUser('Alice', 'alice@example.com');
const company = await factory.createCompany('ACME Corp');
const product = await factory.createProduct('Widget', 19.99, company.id);
```

**Go**:
```go
user := factory.CreateUser("Alice", "alice@example.com")
company := factory.CreateCompany("ACME Corp")
product := factory.CreateProduct("Widget", 19.99, company.ID)
```

### Test Naming Convention

```
test_{feature}_{scenario}_{expected_outcome}
```

Examples:
- `test_query_users_returns_list` - queries return list
- `test_mutation_create_user_persists_to_database` - creates and persists
- `test_invalid_email_raises_validation_error` - error handling
- `test_transaction_isolation_between_tests` - concurrency safety

### Arrange-Act-Assert Pattern

```python
def test_something(db, factory):
    # Arrange: Set up test data
    user = factory.create_user("Alice", "alice@example.com")

    # Act: Execute the code under test
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user["id"],))
    result = cursor.fetchone()

    # Assert: Verify the results
    assert result is not None
    assert result["name"] == "Alice"
```

## Important Notes

### Database Isolation

- **Each test gets a fresh transaction** - no shared state between tests
- **Tests can run in parallel** - each transaction is isolated
- **Automatic cleanup** - rollback deletes all test data (even if test fails)
- **No manual cleanup needed** - transaction handles it

### Real Database Testing

- Tests use **real database behavior**, not mocks
- Catches real performance issues, constraint violations, etc.
- Matches how performance benchmarks test frameworks
- More realistic than mocked testing

### Single Shared Database

- **One PostgreSQL instance** - all 24+ frameworks share it
- **Reduced complexity** - no per-framework database setup
- **Faster execution** - reuse connection pool
- **Easier to debug** - all data in one place

## Coverage Goals

All frameworks should aim for:
- **80%+ code coverage** minimum
- Test happy path scenarios
- Test error/edge cases
- Test data validation
- Test relationships between models

## Troubleshooting

### Database Connection Errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check if listening on 5432
psql -h localhost -U velocitybench -d velocitybench_test -c "SELECT 1"

# If down, start it
docker-compose up -d postgres
```

### Test Isolation Issues

**Problem**: Tests pass alone but fail together

**Causes**:
- Missing transaction cleanup
- Tests modifying shared data
- Tests depending on execution order

**Solutions**:
- Ensure transaction rollback is working
- Each test must be independent
- Never rely on test execution order

### Flaky Tests

**Problem**: Tests sometimes pass, sometimes fail

**Causes**:
- Timing issues in async tests
- Data not properly rolled back
- Shared state between tests

**Solutions**:
- Always await async operations
- Verify transaction isolation
- Use factory pattern consistently

## Customization Examples

### Adding a New Factory Method (Python)

```python
@pytest.fixture
def factory(db):
    class TestFactory:
        # ... existing methods ...

        @staticmethod
        def create_order(user_id: int, total: float):
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "INSERT INTO orders (user_id, total) VALUES (%s, %s) "
                "RETURNING id, user_id, total",
                (user_id, total),
            )
            return dict(cursor.fetchone())

    return TestFactory()
```

### Adding Framework-Specific Tests

Adapt the examples to your framework's resolvers/handlers:

```python
# For a GraphQL resolver
def test_resolver_query_users(db, factory):
    """Test: GraphQL resolver for querying users."""
    from app.schema import query_users

    # Arrange
    factory.create_user("Alice", "alice@example.com")

    # Act
    result = query_users()

    # Assert
    assert len(result) == 1
    assert result[0].name == "Alice"


# For a REST endpoint
def test_endpoint_get_users(db, factory):
    """Test: GET /users endpoint."""
    from app import app
    client = app.test_client()

    # Arrange
    factory.create_user("Alice", "alice@example.com")

    # Act
    response = client.get("/users")

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice"
```

## Performance Tips

- **Batch create test data** - Don't create 100 users in 100 separate tests
- **Reuse connections** - Pool handles connection reuse
- **Keep tests small** - One test per behavior
- **Avoid long transactions** - Tests should run < 5 seconds each

## Environment Variables

Control database connection via environment:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=velocitybench
export DB_PASSWORD=password
export DB_NAME=velocitybench_test

pytest tests/  # Uses environment variables
```

Or in Docker:

```bash
docker run -e DB_HOST=postgres -e DB_PORT=5432 ... pytest tests/
```

## Resources

- **TESTING_STANDARDS.md** - Detailed standards for all languages
- **SCOPE_AND_LIMITATIONS.md** - What we test and don't test
- **.github/workflows/unit-tests.yml** - CI/CD pipeline
- **phase-plans/IMPLEMENTATION_ROADMAP.md** - Full implementation timeline

## Next Steps

1. **Choose your framework** - Pick the first one to test
2. **Copy the template** - Use conftest.py + test_example.py
3. **Start the database** - `docker-compose up -d postgres`
4. **Run tests** - `pytest tests/ --cov=src`
5. **Add your resolvers** - Implement resolver/handler tests
6. **Aim for 80%+** coverage before submitting

---

**Happy Testing! 🚀**
