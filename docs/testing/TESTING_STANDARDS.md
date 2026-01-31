# VelocityBench Testing Standards

**Document Version**: 2.0 (Revised)
**Date**: 2026-01-08
**Status**: Phase 9 - Foundation (Practical Approach)

---

## Overview

This document defines universal testing standards for all VelocityBench frameworks. Every framework tests against a **single shared PostgreSQL database** running in Docker, ensuring consistency and practicality.

**Goal**: 80%+ code coverage across all frameworks with consistent test structure, naming conventions, and real database testing.

**Key Principle**: Test against **real database behavior**, not mocks. This matches how the performance benchmarks work and catches real integration issues.

---

## Universal Testing Principles

### 1. Test Organization

All frameworks follow this directory structure:

```
frameworks/{framework}/
├── src/                              # Production code
│   ├── resolvers.py / index.ts       # or equivalent
│   ├── models.py / models.ts         # or schema definition
│   └── ...
├── tests/                            # All tests
│   ├── test_resolvers.py             # Test resolvers/handlers
│   ├── test_schema.py                # Test schema/types
│   ├── test_integration.py           # Integration tests
│   └── conftest.py                   # Fixtures (Python only)
├── requirements.txt / package.json   # Dependencies
└── pytest.ini / jest.config.js       # Test config (optional)
```

**Simplified structure** - No separation into unit/integration directories. Everything tests the real database.

### 2. Shared PostgreSQL Database

All frameworks connect to the same PostgreSQL instance:

```yaml
# docker-compose.test.yml (or part of main docker-compose.yml)
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: velocitybench
      POSTGRES_PASSWORD: password
      POSTGRES_DB: velocitybench_test
    ports:
      - "5432:5432"
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./database/data.sql:/docker-entrypoint-initdb.d/02-data.sql
```

**One database for all 24+ frameworks** - Reduces complexity, more realistic testing.

### 3. Test Naming Conventions

All tests follow a consistent naming pattern:

```
test_{feature}_{scenario}_{expected_outcome}
```

**Examples**:
- `test_query_users_returns_list` - queries return list
- `test_query_user_by_id_returns_single_user` - filtering works
- `test_mutation_create_user_persists_to_database` - mutations work
- `test_mutation_invalid_data_raises_validation_error` - error handling
- `test_resolver_with_concurrent_requests_maintains_isolation` - concurrency

### 4. Database Testing Pattern

All tests follow the same pattern:

1. **Setup Phase**: Create test data (factory pattern)
2. **Execution Phase**: Call resolver/handler with test data
3. **Assertion Phase**: Verify results in database
4. **Cleanup Phase**: Rollback transaction (automatic via fixture)

**Database Isolation**:
- Each test runs in a **transaction**
- Test data is **rolled back** automatically after each test
- **No cleanup code needed** - transaction handles it
- Tests can **run in parallel** (each has isolated transaction)

### 5. Assertion Quality

Tests must verify:

- **Happy path**: Expected behavior
- **Error cases**: Invalid input handling
- **Edge cases**: Boundary conditions
- **Type safety**: Correct types returned
- **Data integrity**: Database consistency

Assertions should be specific:

```python
# ❌ Bad: Vague assertion
assert result

# ✅ Good: Specific assertion
assert isinstance(result, dict)
assert result["id"] is not None
assert result["name"] == "Alice"
```

---

## Language-Specific Standards

### Python (Strawberry, Graphene, FastAPI, Flask)

**Test Framework**: pytest

**Setup** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing:skip-covered"
asyncio_mode = "auto"

[tool.pytest.ini_options.markers]
slow = "slow tests"
```

**Database Connection** (`tests/conftest.py`):
```python
import pytest
import psycopg2
from psycopg2.extras import DictCursor

DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "velocitybench"
DB_PASSWORD = "password"
DB_NAME = "velocitybench_test"

@pytest.fixture
def db():
    """Connect to shared test database with transaction isolation."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    conn.autocommit = False
    conn.begin()  # Start transaction

    yield conn

    # Cleanup: rollback clears all test data
    conn.rollback()
    conn.close()

@pytest.fixture
def factory(db):
    """Factory for creating test data."""
    class TestFactory:
        @staticmethod
        def create_user(name: str, email: str):
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s) "
                "RETURNING id, name, email",
                (name, email),
            )
            return dict(cursor.fetchone())

        @staticmethod
        def create_company(name: str):
            cursor = db.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "INSERT INTO companies (name) VALUES (%s) RETURNING id, name",
                (name,),
            )
            return dict(cursor.fetchone())

    return TestFactory()
```

**Test Example**:
```python
def test_query_users_returns_list(db, factory):
    """Test: querying users returns a list."""
    # Arrange
    factory.create_user("Alice", "alice@example.com")
    factory.create_user("Bob", "bob@example.com")

    # Act
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT id, name, email FROM users ORDER BY name")
    users = cursor.fetchall()

    # Assert
    assert len(users) == 2
    assert users[0]["name"] == "Alice"
    assert users[1]["name"] == "Bob"

def test_mutation_create_user_persists_to_database(db, factory):
    """Test: creating user persists to database."""
    # Arrange
    user_data = {"name": "Charlie", "email": "charlie@example.com"}

    # Act
    result = factory.create_user(**user_data)

    # Assert
    assert result["name"] == "Charlie"
    assert result["email"] == "charlie@example.com"

    # Verify in database
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (result["id"],))
    db_user = cursor.fetchone()
    assert db_user is not None
    assert db_user["name"] == "Charlie"
```

**Run Tests**:
```bash
cd frameworks/{framework}
pytest tests/ --cov=src
```

---

### TypeScript/Node.js (Apollo, Express)

**Test Framework**: Jest

**Setup** (`jest.config.js`):
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/tests/**/*.test.ts'],
  collectCoverageFrom: ['src/**/*.ts', '!src/**/*.d.ts'],
  coverageThreshold: { global: { lines: 80 } },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
};
```

**Database Connection** (`tests/setup.ts`):
```typescript
import { Pool } from 'pg';

let pool: Pool;

beforeAll(() => {
  pool = new Pool({
    host: 'localhost',
    port: 5432,
    user: 'velocitybench',
    password: 'password',
    database: 'velocitybench_test',
  });
});

afterAll(() => pool.end());

export const getDbConnection = () => pool;

export const withTransaction = async (testFn: () => Promise<void>) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Inject client into test context
    const originalQuery = pool.query.bind(pool);
    pool.query = client.query.bind(client);

    await testFn();

    await client.query('ROLLBACK');
    pool.query = originalQuery;
  } finally {
    client.release();
  }
};

export const factory = {
  async createUser(name: string, email: string) {
    const result = await pool.query(
      'INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email',
      [name, email]
    );
    return result.rows[0];
  },

  async createCompany(name: string) {
    const result = await pool.query(
      'INSERT INTO companies (name) VALUES ($1) RETURNING id, name',
      [name]
    );
    return result.rows[0];
  },
};
```

**Test Example**:
```typescript
import { withTransaction, factory, getDbConnection } from './setup';

describe('User Queries', () => {
  it('should return list of users', async () => {
    await withTransaction(async () => {
      // Arrange
      await factory.createUser('Alice', 'alice@example.com');
      await factory.createUser('Bob', 'bob@example.com');

      // Act
      const pool = getDbConnection();
      const result = await pool.query(
        'SELECT id, name, email FROM users ORDER BY name'
      );
      const users = result.rows;

      // Assert
      expect(users).toHaveLength(2);
      expect(users[0].name).toBe('Alice');
      expect(users[1].name).toBe('Bob');
    });
  });

  it('should create user and persist to database', async () => {
    await withTransaction(async () => {
      // Arrange
      const userData = { name: 'Charlie', email: 'charlie@example.com' };

      // Act
      const user = await factory.createUser(userData.name, userData.email);

      // Assert
      expect(user.name).toBe('Charlie');
      expect(user.email).toBe('charlie@example.com');
    });
  });
});
```

**Run Tests**:
```bash
cd frameworks/{framework}
npm test -- --coverage
```

---

### Go (gqlgen, gin, graphql-go)

**Test Framework**: Go testing + testify

**Database Connection** (`test_helpers.go`):
```go
package main

import (
	"database/sql"
	"testing"

	"github.com/stretchr/testify/require"
	_ "github.com/lib/pq"
)

func setupDB(t *testing.T) *sql.DB {
	db, err := sql.Open("postgres",
		"postgres://velocitybench:password@localhost:5432/velocitybench_test?sslmode=disable")
	require.NoError(t, err)

	err = db.Ping()
	require.NoError(t, err)

	return db
}

func withTransaction(t *testing.T, db *sql.DB, testFn func(*sql.Tx)) {
	tx, err := db.Begin()
	require.NoError(t, err)
	defer tx.Rollback()

	testFn(tx)
}

type TestFactory struct {
	tx *sql.Tx
	t  *testing.T
}

func (f *TestFactory) CreateUser(name, email string) map[string]interface{} {
	row := f.tx.QueryRow(
		"INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email",
		name, email,
	)

	var id int
	var n, e string
	err := row.Scan(&id, &n, &e)
	require.NoError(f.t, err)

	return map[string]interface{}{"id": id, "name": n, "email": e}
}

func (f *TestFactory) CreateCompany(name string) map[string]interface{} {
	row := f.tx.QueryRow(
		"INSERT INTO companies (name) VALUES ($1) RETURNING id, name",
		name,
	)

	var id int
	var n string
	err := row.Scan(&id, &n)
	require.NoError(f.t, err)

	return map[string]interface{}{"id": id, "name": n}
}
```

**Test Example** (`resolvers_test.go`):
```go
package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestQueryUsers(t *testing.T) {
	db := setupDB(t)
	defer db.Close()

	withTransaction(t, db, func(tx *sql.Tx) {
		// Arrange
		factory := &TestFactory{tx: tx, t: t}
		factory.CreateUser("Alice", "alice@example.com")
		factory.CreateUser("Bob", "bob@example.com")

		// Act
		rows, err := tx.Query("SELECT id, name, email FROM users ORDER BY name")
		require.NoError(t, err)
		defer rows.Close()

		var users []map[string]interface{}
		for rows.Next() {
			var id int
			var name, email string
			err := rows.Scan(&id, &name, &email)
			require.NoError(t, err)
			users = append(users, map[string]interface{}{
				"id": id, "name": name, "email": email,
			})
		}

		// Assert
		assert.Equal(t, 2, len(users))
		assert.Equal(t, "Alice", users[0]["name"])
		assert.Equal(t, "Bob", users[1]["name"])
	})
}

func TestCreateUser(t *testing.T) {
	db := setupDB(t)
	defer db.Close()

	withTransaction(t, db, func(tx *sql.Tx) {
		// Arrange
		factory := &TestFactory{tx: tx, t: t}
		userData := map[string]string{"name": "Charlie", "email": "charlie@example.com"}

		// Act
		user := factory.CreateUser(userData["name"], userData["email"])

		// Assert
		assert.Equal(t, "Charlie", user["name"])
		assert.Equal(t, "charlie@example.com", user["email"])
	})
}
```

**Run Tests**:
```bash
cd frameworks/{framework}
go test -v -cover ./...
```

---

### Java (Spring Boot)

**Test Framework**: JUnit 5 + Testcontainers (optional, but can use shared DB)

**Database Connection** (`src/test/java/TestBase.java`):
```java
@SpringBootTest
public abstract class TestBase {

    protected static final String DB_URL = "jdbc:postgresql://localhost:5432/velocitybench_test";
    protected static final String DB_USER = "velocitybench";
    protected static final String DB_PASSWORD = "password";

    @Autowired
    protected JdbcTemplate jdbcTemplate;

    @BeforeEach
    public void setUp() {
        // Start transaction for test
        jdbcTemplate.execute("BEGIN");
    }

    @AfterEach
    public void tearDown() {
        // Rollback test transaction
        try {
            jdbcTemplate.execute("ROLLBACK");
        } catch (Exception e) {
            // Already rolled back
        }
    }

    protected Map<String, Object> createUser(String name, String email) {
        return jdbcTemplate.queryForMap(
            "INSERT INTO users (name, email) VALUES (?, ?) " +
            "RETURNING id, name, email",
            name, email
        );
    }

    protected Map<String, Object> createCompany(String name) {
        return jdbcTemplate.queryForMap(
            "INSERT INTO companies (name) VALUES (?) RETURNING id, name",
            name
        );
    }
}
```

**Test Example** (`src/test/java/UserResolverTest.java`):
```java
public class UserResolverTest extends TestBase {

    @Test
    public void testQueryUsersReturnsAllUsers() {
        // Arrange
        createUser("Alice", "alice@example.com");
        createUser("Bob", "bob@example.com");

        // Act
        List<Map<String, Object>> users = jdbcTemplate.queryForList(
            "SELECT id, name, email FROM users ORDER BY name"
        );

        // Assert
        assertEquals(2, users.size());
        assertEquals("Alice", users.get(0).get("name"));
        assertEquals("Bob", users.get(1).get("name"));
    }
}
```

**Run Tests**:
```bash
cd frameworks/{framework}
mvn test
```

---

### Rust (Async-graphql, Actix)

**Test Framework**: Tokio + sqlx

**Test Example**:
```rust
#[tokio::test]
async fn test_query_users_returns_list() {
    // Setup
    let db_url = "postgres://velocitybench:password@localhost:5432/velocitybench_test";
    let pool = PgPoolOptions::new()
        .connect(db_url)
        .await
        .unwrap();

    let mut tx = pool.begin().await.unwrap();

    // Arrange: Create test data
    sqlx::query("INSERT INTO users (name, email) VALUES ($1, $2)")
        .bind("Alice")
        .bind("alice@example.com")
        .execute(&mut *tx)
        .await
        .unwrap();

    // Act: Query users
    let users: Vec<(i32, String, String)> = sqlx::query_as(
        "SELECT id, name, email FROM users ORDER BY name"
    )
    .fetch_all(&mut *tx)
    .await
    .unwrap();

    // Assert
    assert_eq!(users.len(), 1);
    assert_eq!(users[0].1, "Alice");

    // Cleanup (automatic on drop)
    tx.rollback().await.unwrap();
}
```

**Run Tests**:
```bash
cd frameworks/{framework}
cargo test
```

---

### PHP (Laravel)

**Test Framework**: PHPUnit

**Test Example** (`tests/Feature/UserTest.php`):
```php
class UserTest extends TestCase {
    protected function setUp(): void {
        parent::setUp();
        // Use in-memory transaction
        DB::beginTransaction();
    }

    protected function tearDown(): void {
        // Rollback transaction
        DB::rollBack();
        parent::tearDown();
    }

    public function test_query_users_returns_list() {
        // Arrange
        User::create(['name' => 'Alice', 'email' => 'alice@example.com']);
        User::create(['name' => 'Bob', 'email' => 'bob@example.com']);

        // Act
        $users = User::orderBy('name')->get();

        // Assert
        $this->assertCount(2, $users);
        $this->assertEquals('Alice', $users[0]->name);
        $this->assertEquals('Bob', $users[1]->name);
    }
}
```

**Run Tests**:
```bash
cd frameworks/{framework}
php artisan test
```

---

### Ruby (Rails)

**Test Framework**: RSpec

**Test Example** (`spec/models/user_spec.rb`):
```ruby
RSpec.describe User do
  around { |example| User.transaction { example.run; raise ActiveRecord::Rollback } }

  describe 'queries' do
    it 'returns list of all users' do
      # Arrange
      User.create(name: 'Alice', email: 'alice@example.com')
      User.create(name: 'Bob', email: 'bob@example.com')

      # Act
      users = User.order(:name)

      # Assert
      expect(users.count).to eq(2)
      expect(users[0].name).to eq('Alice')
      expect(users[1].name).to eq('Bob')
    end
  end
end
```

**Run Tests**:
```bash
cd frameworks/{framework}
bundle exec rspec
```

---

### C# (.NET)

**Test Framework**: xUnit

**Test Example**:
```csharp
public class UserTests : IAsyncLifetime {
    private readonly NpgsqlConnection _connection;

    public UserTests() {
        _connection = new NpgsqlConnection(
            "Host=localhost;Username=velocitybench;Password=password;Database=velocitybench_test"
        );
    }

    public async Task InitializeAsync() {
        await _connection.OpenAsync();
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "BEGIN";
        await cmd.ExecuteNonQueryAsync();
    }

    public async Task DisposeAsync() {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "ROLLBACK";
        await cmd.ExecuteNonQueryAsync();
        await _connection.CloseAsync();
    }

    [Fact]
    public async Task QueryUsers_ReturnsAllUsers() {
        // Arrange
        await CreateUser("Alice", "alice@example.com");
        await CreateUser("Bob", "bob@example.com");

        // Act
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "SELECT name FROM users ORDER BY name";
        using var reader = await cmd.ExecuteReaderAsync();

        var users = new List<string>();
        while (await reader.ReadAsync()) {
            users.Add(reader.GetString(0));
        }

        // Assert
        Assert.Equal(2, users.Count);
        Assert.Equal("Alice", users[0]);
        Assert.Equal("Bob", users[1]);
    }

    private async Task CreateUser(string name, string email) {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "INSERT INTO users (name, email) VALUES (@name, @email)";
        cmd.Parameters.AddWithValue("@name", name);
        cmd.Parameters.AddWithValue("@email", email);
        await cmd.ExecuteNonQueryAsync();
    }
}
```

**Run Tests**:
```bash
cd frameworks/{framework}
dotnet test
```

---

## Test Checklist

Before submitting tests, verify:

### Code Quality
- [ ] Tests are isolated and independent
- [ ] Test names clearly describe what is tested
- [ ] All assertions are specific and meaningful
- [ ] No hardcoded values (use factory instead)
- [ ] Code is DRY (Don't Repeat Yourself)

### Database Testing
- [ ] All tests use shared PostgreSQL database
- [ ] Transaction isolation handles cleanup
- [ ] Tests can run in parallel
- [ ] No data persists between tests
- [ ] All test data created via factory

### Coverage
- [ ] 80%+ code coverage (or better)
- [ ] Happy path tested
- [ ] Error cases tested
- [ ] Edge cases identified and tested

### Performance
- [ ] Tests run quickly (< 5 seconds each)
- [ ] Database operations optimized
- [ ] No unnecessary queries
- [ ] Parallel execution possible

---

## Running Tests

### Start Shared Database

```bash
# From repository root
docker-compose up -d postgres

# Verify database is ready
sleep 2
psql -h localhost -U velocitybench -d velocitybench_test -c "SELECT 1"
```

### Run All Tests (All Frameworks)

```bash
# Python
cd frameworks/strawberry && pytest tests/ --cov=src && cd ../..

# TypeScript
cd frameworks/apollo-server && npm test && cd ../..

# Go
cd frameworks/go-gqlgen && go test -v ./... && cd ../..

# Java
cd frameworks/java-spring-boot && mvn test && cd ../..
```

### Run Tests for Single Framework

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

### Local Development

```bash
# Terminal 1: Start database
docker-compose up postgres

# Terminal 2: Run tests
cd frameworks/{framework}
npm test --watch  # or equivalent for your language
```

---

## Troubleshooting

### Database Connection Errors

**Problem**: Tests fail to connect to database

**Solution**: Verify PostgreSQL is running
```bash
psql -h localhost -U velocitybench -d velocitybench_test -c "SELECT 1"
```

If connection fails:
```bash
docker-compose up -d postgres
docker-compose logs postgres
```

### Test Isolation Issues

**Problem**: Tests pass individually but fail when run together

**Solution**: Verify transaction isolation
- Python: Use `conn.begin()` and `conn.rollback()`
- TypeScript: Use transaction wrapper
- Go: Use `tx.Rollback()` in defer
- Java: Use `@Transactional` or manual transaction
- Others: Check language-specific transaction support

### Flaky Tests

**Problem**: Tests sometimes pass, sometimes fail

**Causes**:
- Shared test data not properly cleaned up
- Tests depend on execution order
- Timing issues in async tests

**Solutions**:
- Use transaction rollback for all tests
- Never rely on test execution order
- Always await async operations

---

## CI/CD Integration Requirements

All new frameworks **must be added to the CI pipeline** in `.github/workflows/unit-tests.yml`. This ensures:

### Required for All Frameworks

1. **Test Runner Integration**
   - Framework tests must be executable via standard command (pytest, npm test, go test, cargo test, etc.)
   - Tests must run without user interaction
   - Tests must exit with code 0 on success, non-zero on failure

2. **Coverage Reporting**
   - Framework must generate coverage reports in standard format
   - Coverage format: `coverage.xml` (Cobertura), `coverage.out` (Go), or equivalent
   - Coverage must be uploaded to Codecov for tracking

3. **No Silent Failures**
   - ❌ NEVER use `|| echo "No tests found"` (hides real failures)
   - ✅ ALWAYS exit with error code: `|| exit 1`
   - Test failures must be visible in CI logs

4. **Matrix Placement**
   - Add framework to appropriate language matrix in CI workflow
   - Or create new job if using unique build tool (see jvm-tests, hasura-tests examples)
   - Update `needs:` dependencies in coverage-check and test-status jobs

### Language-Specific CI Matrix

| Language | Test Runner | Coverage Format | Example Frameworks |
|----------|-------------|-----------------|-------------------|
| Python | pytest | coverage.xml | strawberry, graphene, fastapi-rest, ariadne |
| TypeScript | npm test (Vitest/Jest) | coverage/ | apollo-server, express-rest, graphql-yoga |
| Go | go test | coverage.out | go-gqlgen, gin-rest, graphql-go |
| Java (Maven) | mvn test | target/site/jacoco/jacoco.xml | java-spring-boot |
| Java (Other) | Custom | target/site/jacoco/jacoco.xml | Gradle, sbt |
| Rust | cargo test | (optional) | async-graphql, actix-web-rest |
| PHP | PHPUnit/artisan | coverage.xml | php-laravel, webonyx-graphql-php |
| Ruby | RSpec/Minitest | (optional) | ruby-rails, hanami |
| C# | dotnet test | opencover format | csharp-dotnet |
| Special | Custom | framework-dependent | hasura |

### Test Validation Strategy

Before adding framework to CI:

1. **Local Validation**
   ```bash
   cd frameworks/your-framework
   # Run your test command
   # Verify coverage reports generate
   # Confirm test command fails properly on test failure
   ```

2. **CI Workflow Addition**
   - Add to appropriate matrix or create new job
   - Update dependencies in coverage-check
   - Update failure check logic
   - Update summary generation

3. **Test Merge Validation**
   - Run CI workflow on PR
   - Verify test results show in summary
   - Confirm coverage uploads to Codecov
   - Verify test failure detection works (introduce intentional failure)

---

## CI/CD Pipeline

The GitHub Actions pipeline automatically:
1. Starts PostgreSQL container
2. Loads database schema
3. Runs all tests for all frameworks
4. Reports coverage
5. Shows test results

See `.github/workflows/unit-tests.yml` for configuration.

---

## Further Reading

- **SCOPE_AND_LIMITATIONS.md** - What we test and don't test
- **testing-templates/** - Reusable code templates
- **phase-plans/IMPLEMENTATION_ROADMAP.md** - Full implementation timeline
- **.github/workflows/unit-tests.yml** - CI/CD pipeline configuration
