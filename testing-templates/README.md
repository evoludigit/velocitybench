# VelocityBench Testing Templates

Reusable test templates for implementing unit and integration tests across all VelocityBench frameworks.

## Overview

These templates provide a starting point for testing each framework. They include:

- ✅ Database connection helpers
- ✅ Test factory pattern for creating test data
- ✅ Unit test examples
- ✅ Integration test examples
- ✅ Best practices for each language
- ✅ Common testing patterns

## Files

### Python

**`conftest.py`** - pytest fixtures and test helpers

Features:
- Session and per-test database fixtures with transaction isolation
- `TestDatabase` class for connection management
- `TestFactory` for creating test data
- Custom markers for test categorization (@unit, @integration, @slow, @async)
- Example factory methods (create_user, create_company, create_product)

**`test_example.py`** - Complete test example suite

Includes:
- Unit tests (validation, transformation, parametrized tests)
- Integration tests (CRUD operations, complex queries)
- Test fixtures and helpers
- Comments explaining the Arrange-Act-Assert pattern

### TypeScript/Jest

**`test.example.ts`** - Jest test configuration and examples

Includes:
- `TestDatabase` class with pg Pool for connection management
- `TestFactory` for async test data creation
- Jest setup with beforeEach/afterEach
- Unit tests (validation, formatting, parametrized tests)
- Integration tests (CRUD, aggregation queries)
- Error handling patterns

### Go

**`example_test.go`** - Go testing patterns using testify

Includes:
- `TestDB` helper with connection management
- Test data models (User, Company, Product)
- `TestFactory` pattern for creating test data
- Unit tests (validation, formatting, assertions)
- Integration tests (CRUD operations)
- Testify assertions and require patterns

## How to Use

### For Python Frameworks

1. Copy the fixtures into your framework:
   ```bash
   cp testing-templates/conftest.py frameworks/{framework}/tests/
   ```

2. Copy and rename the example test file:
   ```bash
   cp testing-templates/test_example.py frameworks/{framework}/tests/test_resolvers.py
   ```

3. Update the imports and database connection details in both files

4. Customize the factory methods for your data models:
   ```python
   # Add custom factory methods for your models
   def create_order(self, user_id: int, total: float):
       cursor = self.db.execute(
           "INSERT INTO orders (user_id, total) VALUES (%s, %s) "
           "RETURNING id, user_id, total",
           (user_id, total),
       )
       row = cursor.fetchone()
       self.db.connection.commit()
       return dict(row) if row else None
   ```

5. Add your resolver/handler tests following the template patterns

6. Run tests:
   ```bash
   cd frameworks/{framework}
   pytest tests/ --cov=src
   ```

### For TypeScript Frameworks

1. Copy the example test file:
   ```bash
   cp testing-templates/test.example.ts frameworks/{framework}/tests/resolvers.test.ts
   ```

2. Create Jest configuration (if not present):
   ```bash
   npx jest --init
   ```

3. Update imports and database connection in the test file

4. Add custom factory methods for your models:
   ```typescript
   async createOrder(userId: number, total: number): Promise<any> {
     const rows = await this.db.query(
       'INSERT INTO orders (user_id, total) VALUES ($1, $2) ' +
       'RETURNING id, user_id, total',
       [userId, total]
     );
     return rows[0];
   }
   ```

5. Add resolver/handler tests following the template patterns

6. Run tests:
   ```bash
   npm test -- --coverage
   ```

### For Go Frameworks

1. Copy the example test file:
   ```bash
   cp testing-templates/example_test.go frameworks/{framework}/
   ```

2. Update imports (go-sql-driver, postgres connection string)

3. Add custom factory methods:
   ```go
   func (f *TestFactory) CreateOrder(userID int, total float64) *Order {
       row := f.db.QueryRow(
           "INSERT INTO orders (user_id, total) VALUES ($1, $2) "+
               "RETURNING id, user_id, total",
           userID, total,
       )
       var order Order
       err := row.Scan(&order.ID, &order.UserID, &order.Total)
       require.NoError(f.t, err)
       return &order
   }
   ```

4. Add handler/resolver tests following the template patterns

5. Run tests:
   ```bash
   go test -v -cover ./...
   ```

## Key Patterns Explained

### Database Isolation

Each test gets a clean database state via transaction isolation:

**Python**:
```python
@pytest.fixture
def db(test_db):
    """Per-test database with transaction isolation."""
    test_db.begin_transaction()  # Start transaction
    yield db
    test_db.rollback()  # Rollback after test
```

**TypeScript**:
```typescript
beforeEach(async () => {
  db = new TestDatabase();
  await db.connect();
  // Clean tables
  await db.query('DELETE FROM orders');
  await db.query('DELETE FROM products');
  await db.query('DELETE FROM users');
  await db.query('DELETE FROM companies');
});

afterEach(async () => {
  await db.close();
});
```

**Go**:
```go
func TestGetUserByID(t *testing.T) {
    db := setupTestDB(t)
    defer db.Close()

    // Clean up
    db.Exec("DELETE FROM users")

    // Test code
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

**Examples**:
- `test_query_users_returns_list` - queries return list
- `test_create_user_persists_to_database` - creates user
- `test_invalid_email_raises_validation_error` - error handling
- `test_concurrent_requests_maintain_isolation` - concurrency

## Testing Standards

All tests should follow these standards (see `TESTING_STANDARDS.md`):

- ✅ **Isolated**: No dependencies on other tests
- ✅ **Repeatable**: Runs consistently in any order
- ✅ **Deterministic**: Same result every time
- ✅ **Atomic**: Either fully succeeds or fully fails
- ✅ **Self-contained**: Sets up all required data

### Minimum Coverage

Target 80%+ code coverage for all frameworks:

```bash
# Python
pytest tests/ --cov=src --cov-report=html

# TypeScript
npm test -- --coverage

# Go
go test -cover ./...
```

## Common Issues

### Database Connection Errors

**Problem**: Tests fail to connect to database

**Solution**: Verify PostgreSQL is running:
```bash
psql -h localhost -U velocitybench -d velocitybench_test -c "SELECT 1"
```

### Test Isolation Failures

**Problem**: Tests pass individually but fail when run together

**Solution**: Ensure database cleanup between tests:
- Python: Use transaction rollback in fixture
- TypeScript: Delete/truncate tables in beforeEach
- Go: Call Exec("DELETE FROM ...") at test start

### Timeout Errors

**Problem**: Tests take too long to run

**Solution**:
- Optimize database queries
- Mock external dependencies
- Reduce test data size
- Increase timeout in test configuration

## Next Steps

1. **Choose your framework and language**
   - Find the matching template
   - Copy it to your framework's tests directory

2. **Read the relevant section in TESTING_STANDARDS.md**
   - Language-specific best practices
   - Test organization patterns
   - Common patterns and anti-patterns

3. **Customize the template**
   - Update database connection details
   - Add your framework's models/resolvers
   - Implement factory methods for your data

4. **Write tests**
   - Start with unit tests (no database)
   - Add integration tests (with database)
   - Aim for 80%+ coverage

5. **Run tests locally**
   - Verify all tests pass
   - Check coverage
   - Commit with meaningful message

## Additional Resources

- **SCOPE_AND_LIMITATIONS.md** - What we test and don't test
- **TESTING_STANDARDS.md** - Detailed testing standards by language
- **phase-plans/IMPLEMENTATION_ROADMAP.md** - Full implementation timeline
- **.github/workflows/unit-tests.yml** - CI/CD pipeline configuration

## Questions?

See the relevant section in `TESTING_STANDARDS.md` for your language, or refer to the complete framework documentation in `docs/`.

---

**Happy Testing! 🚀**
