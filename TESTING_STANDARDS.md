# VelocityBench Testing Standards

**Document Version**: 1.0
**Date**: 2026-01-08
**Status**: Phase 9 - Foundation

---

## Overview

This document defines universal testing standards for all VelocityBench frameworks. Every framework must follow these standards to ensure consistency, maintainability, and publication-ready quality.

**Goal**: 80%+ code coverage across all frameworks with consistent test structure and naming conventions.

---

## Universal Testing Principles

### 1. Test Organization

All frameworks follow this directory structure:

```
frameworks/{language}/{framework}/
├── src/                          # Production code
│   ├── resolvers.py              # or equivalent
│   ├── models.py                 # or schema definition
│   └── ...
├── tests/                        # All tests
│   ├── __init__.py              # Test marker (Python)
│   ├── unit/                    # Unit tests (isolated)
│   │   ├── test_resolvers.py
│   │   ├── test_models.py
│   │   └── test_validation.py
│   ├── integration/             # Integration tests (with database)
│   │   ├── test_queries.py
│   │   ├── test_mutations.py
│   │   └── test_schema.py
│   └── conftest.py              # Fixtures (Python)
└── pyproject.toml               # Config (Python)
```

### 2. Test Naming Conventions

All tests follow a consistent naming pattern:

```
test_{feature}_{scenario}_{expected_outcome}
```

**Examples**:
- `test_query_users_returns_list` - queries return list
- `test_query_user_by_id_returns_single_user` - filtering works
- `test_query_invalid_id_raises_validation_error` - error handling
- `test_mutation_create_user_persists_to_database` - mutations work
- `test_concurrent_requests_maintain_isolation` - concurrency safety

### 3. Test Independence

Each test must be:

- **Isolated**: No dependencies on other tests
- **Repeatable**: Runs consistently in any order
- **Deterministic**: Same result every time
- **Atomic**: Either fully succeeds or fully fails
- **Self-contained**: Sets up all required data

### 4. Database Testing

All integration tests with database follow:

1. **Setup Phase**: Create test data
2. **Execution Phase**: Run test
3. **Assertion Phase**: Verify results
4. **Cleanup Phase**: Reset database state

Database isolation strategy:
- Fresh database or transaction rollback per test
- No shared state between tests
- Deterministic test data (same values every run)

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
assert "id" in result
assert result["id"] == 123
assert result["email"] == "test@example.com"
```

---

## Language-Specific Standards

### Python (Strawberry, Graphene, FastAPI, Flask)

**Test Framework**: pytest

**Configuration** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
markers = [
    "unit: unit tests",
    "integration: integration tests",
    "slow: slow tests"
]
```

**Fixtures** (`tests/conftest.py`):
```python
import pytest
from database import create_test_db, drop_test_db

@pytest.fixture(scope="session")
def test_db():
    """Create test database once per session"""
    db = create_test_db()
    yield db
    drop_test_db(db)

@pytest.fixture
def db(test_db):
    """Fresh database per test via transaction rollback"""
    test_db.begin()
    yield test_db
    test_db.rollback()

@pytest.fixture
def client(app, db):
    """GraphQL/REST client for testing"""
    return app.test_client()
```

**Test Template**:
```python
import pytest
from models import User
from queries import QueryResolvers

@pytest.mark.unit
class TestQueryResolvers:
    """Tests for resolver functions"""

    def test_query_users_returns_list(self, db):
        # Arrange
        user1 = User.create(db, name="Alice", email="alice@example.com")
        user2 = User.create(db, name="Bob", email="bob@example.com")

        # Act
        result = QueryResolvers.users(None)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "Alice"

@pytest.mark.integration
class TestUserQueries:
    """Tests for user queries with database"""

    async def test_query_user_by_id(self, client, db):
        # Arrange
        user = User.create(db, name="Alice", email="alice@example.com")

        # Act
        response = await client.query(f"""
            query {{
                user(id: "{user.id}") {{
                    id
                    name
                    email
                }}
            }}
        """)

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]["user"]
        assert data["id"] == str(user.id)
        assert data["name"] == "Alice"
```

**Minimum Coverage**: 80% of production code

**Run Tests**:
```bash
cd frameworks/python/{framework}
pytest --cov=src
pytest tests/unit/  # unit tests only
pytest -m integration  # integration tests only
```

---

### TypeScript/Node.js (Apollo, Express, PostGraphile)

**Test Framework**: Jest

**Configuration** (`jest.config.js`):
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/?(*.)+(spec|test).ts?(x)'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

**Test Template**:
```typescript
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { createTestClient } from './test-utils';
import { User } from '../src/models';

describe('Query Resolvers', () => {
  let client: any;
  let db: any;

  beforeEach(async () => {
    db = await setupTestDatabase();
    client = createTestClient(db);
  });

  afterEach(async () => {
    await teardownTestDatabase(db);
  });

  it('returns list of users', async () => {
    // Arrange
    const user1 = await User.create(db, {
      name: 'Alice',
      email: 'alice@example.com',
    });

    // Act
    const result = await client.query(`
      query {
        users {
          id
          name
          email
        }
      }
    `);

    // Assert
    expect(result.data.users).toBeDefined();
    expect(result.data.users).toHaveLength(1);
    expect(result.data.users[0].name).toBe('Alice');
  });
});
```

**Test Utilities** (`tests/test-utils.ts`):
```typescript
export async function setupTestDatabase() {
  // Create fresh database for test
}

export function createTestClient(db: any) {
  // Return GraphQL/REST client
}

export async function teardownTestDatabase(db: any) {
  // Clean up database
}
```

**Minimum Coverage**: 80% of production code

**Run Tests**:
```bash
cd frameworks/typescript/{framework}
npm test
npm test -- --coverage  # with coverage report
npm test -- --testPathPattern=unit  # unit tests only
```

---

### Go (gqlgen, gin, graphql-go)

**Test Framework**: testing (Go standard library) + testify

**Configuration** (`go.mod`):
```
require (
    github.com/stretchr/testify v1.8.4
    github.com/DATA-DOG/go-sqlmock v1.5.0
)
```

**Test Template** (`resolvers_test.go`):
```go
package resolvers

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestQueryUsers(t *testing.T) {
    // Arrange
    db := setupTestDB(t)
    defer db.Close()

    user1 := createTestUser(t, db, "Alice", "alice@example.com")
    user2 := createTestUser(t, db, "Bob", "bob@example.com")

    ctx := context.Background()
    resolver := NewQueryResolver(db)

    // Act
    users, err := resolver.Users(ctx)

    // Assert
    require.NoError(t, err)
    assert.Equal(t, 2, len(users))
    assert.Equal(t, "Alice", users[0].Name)
}
```

**Test Helpers** (`test_helpers.go`):
```go
func setupTestDB(t *testing.T) *sql.DB {
    // Create fresh test database
}

func createTestUser(t *testing.T, db *sql.DB, name, email string) *User {
    // Create test data
}
```

**Code Coverage**:
```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

**Minimum Coverage**: 80% of production code

**Run Tests**:
```bash
cd frameworks/go/{framework}
go test ./...  # all tests
go test -run TestQuery ./...  # specific tests
go test -v -cover ./...  # verbose with coverage
```

---

### Java (Spring Boot)

**Test Framework**: JUnit 5 + Mockito + TestContainers

**Dependencies** (`pom.xml`):
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <version>3.0.0</version>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>testcontainers</artifactId>
    <version>1.17.6</version>
    <scope>test</scope>
</dependency>
```

**Test Template** (`UserResolverTest.java`):
```java
@SpringBootTest
class UserResolverTest {

    @Autowired
    private UserResolver resolver;

    @Autowired
    private UserRepository repository;

    @BeforeEach
    void setUp() {
        repository.deleteAll();
    }

    @Test
    void testQueryUsers() {
        // Arrange
        User user1 = new User();
        user1.setName("Alice");
        user1.setEmail("alice@example.com");
        repository.save(user1);

        // Act
        List<User> users = resolver.users();

        // Assert
        assertNotNull(users);
        assertEquals(1, users.size());
        assertEquals("Alice", users.get(0).getName());
    }
}
```

**Code Coverage** (`jacoco-maven-plugin`):
```bash
mvn test
mvn jacoco:report  # generates coverage report
```

**Minimum Coverage**: 80% of production code

---

### Rust (Async-graphql, Actix)

**Test Framework**: Rust built-in + tokio for async

**Test Template** (`src/resolvers.rs`):
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tokio::test;

    #[test]
    async fn test_query_users() {
        // Arrange
        let db = setup_test_db().await;
        let user = create_test_user(&db, "Alice", "alice@example.com").await;

        // Act
        let users = query_users(&db).await;

        // Assert
        assert_eq!(users.len(), 1);
        assert_eq!(users[0].name, "Alice");
    }
}
```

**Code Coverage**:
```bash
cargo tarpaulin --out Html
```

**Minimum Coverage**: 80% of production code

**Run Tests**:
```bash
cargo test
cargo test --test '*' -- --nocapture
```

---

### PHP (Laravel)

**Test Framework**: PHPUnit

**Configuration** (`phpunit.xml`):
```xml
<phpunit>
    <testsuites>
        <testsuite name="Unit">
            <directory suffix="Test.php">./tests/Unit</directory>
        </testsuite>
        <testsuite name="Feature">
            <directory suffix="Test.php">./tests/Feature</directory>
        </testsuite>
    </testsuites>
</phpunit>
```

**Test Template** (`tests/Unit/UserResolverTest.php`):
```php
namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use App\Models\User;
use App\Resolvers\UserResolver;

class UserResolverTest extends TestCase
{
    public function test_query_users_returns_array()
    {
        // Arrange
        $resolver = new UserResolver();

        // Act
        $users = $resolver->users();

        // Assert
        $this->assertIsArray($users);
    }
}
```

**Code Coverage**:
```bash
phpunit --coverage-html coverage/
```

**Minimum Coverage**: 80% of production code

---

### Ruby (Rails)

**Test Framework**: RSpec

**Configuration** (`spec/spec_helper.rb`):
```ruby
RSpec.configure do |config|
  config.require 'simplecov'
  SimpleCov.start do
    add_filter '/spec/'
  end
end
```

**Test Template** (`spec/resolvers/user_resolver_spec.rb`):
```ruby
require 'rails_helper'

RSpec.describe UserResolver do
  describe '#users' do
    it 'returns list of users' do
      # Arrange
      create(:user, name: 'Alice', email: 'alice@example.com')
      create(:user, name: 'Bob', email: 'bob@example.com')

      # Act
      result = UserResolver.new.users

      # Assert
      expect(result).to be_a(Array)
      expect(result.length).to eq(2)
      expect(result[0].name).to eq('Alice')
    end
  end
end
```

**Code Coverage**:
```bash
rspec  # runs all tests
rspec --format documentation
```

**Minimum Coverage**: 80% of production code

---

### C# (.NET)

**Test Framework**: xUnit + Moq

**Test Template** (`UserResolverTests.cs`):
```csharp
public class UserResolverTests
{
    [Fact]
    public async Task QueryUsers_ReturnsListOfUsers()
    {
        // Arrange
        var db = new TestDbContext();
        var user = new User { Name = "Alice", Email = "alice@example.com" };
        db.Users.Add(user);
        await db.SaveChangesAsync();

        var resolver = new UserResolver(db);

        // Act
        var result = await resolver.Users();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal("Alice", result[0].Name);
    }
}
```

**Code Coverage**:
```bash
dotnet test /p:CollectCoverage=true
```

**Minimum Coverage**: 80% of production code

---

## Common Test Patterns

### Pattern 1: Database Isolation

**Goal**: Each test gets clean database state

**Python**:
```python
@pytest.fixture
def clean_db(db):
    """Transaction-based isolation"""
    db.session.begin_nested()
    yield db.session
    db.session.rollback()
```

**Go**:
```go
func TestWithDB(t *testing.T) {
    db := setupTestDB(t)
    defer func() {
        db.Exec("ROLLBACK")
    }()
    // test code
}
```

### Pattern 2: Factory/Builder Pattern

Create test data consistently:

**Python**:
```python
class UserFactory:
    @staticmethod
    def create(db, name="Test User", email="test@example.com"):
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()
        return user
```

**TypeScript**:
```typescript
export function createTestUser(
  db: any,
  overrides: Partial<User> = {}
): User {
  return new User({
    name: 'Test User',
    email: 'test@example.com',
    ...overrides,
  });
}
```

### Pattern 3: Parametrized Tests

Test multiple scenarios:

**Python**:
```python
@pytest.mark.parametrize("input,expected", [
    ("Alice", "alice"),
    ("Bob Smith", "bob smith"),
    ("123 ABC", "123 abc"),
])
def test_normalize_name(input, expected):
    assert normalize_name(input) == expected
```

**TypeScript**:
```typescript
describe.each([
  ['Alice', 'alice'],
  ['Bob Smith', 'bob smith'],
  ['123 ABC', '123 abc'],
])('normalizeName(%s)', (input, expected) => {
  it(`returns ${expected}`, () => {
    expect(normalizeName(input)).toBe(expected);
  });
});
```

### Pattern 4: Mocking External Dependencies

**Python**:
```python
from unittest.mock import patch

@patch('external_service.get_data')
def test_resolver_with_mocked_service(mock_service):
    mock_service.return_value = {'id': 1, 'name': 'Test'}
    result = resolver.get_data()
    assert result['name'] == 'Test'
    mock_service.assert_called_once()
```

**TypeScript**:
```typescript
jest.mock('../external-service');

it('calls external service', async () => {
  const mockService = require('../external-service');
  mockService.getData.mockResolvedValue({ id: 1, name: 'Test' });

  const result = await resolver.getData();
  expect(result.name).toBe('Test');
  expect(mockService.getData).toHaveBeenCalled();
});
```

---

## Test Checklist

Before submitting tests, verify:

### Code Quality
- [ ] Tests are isolated and independent
- [ ] Test names clearly describe what is tested
- [ ] All assertions are specific and meaningful
- [ ] No magic numbers or hardcoded values
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] Fixtures/setup is documented

### Coverage
- [ ] Happy path tested
- [ ] Error cases tested
- [ ] Edge cases identified and tested
- [ ] Type safety verified (where applicable)
- [ ] Database integrity verified

### Database Tests
- [ ] Database state is reset between tests
- [ ] All data is created by test (not shared)
- [ ] Database cleanup is verified
- [ ] Transaction isolation tested
- [ ] Concurrent access safety tested

### Performance
- [ ] Tests run in < 5 seconds each
- [ ] Database fixtures are optimized
- [ ] Unnecessary I/O minimized
- [ ] Parallel test execution possible

### Documentation
- [ ] Test purpose is clear from name
- [ ] Complex logic has comments
- [ ] Expected behavior documented
- [ ] Known limitations noted

---

## Running All Tests

### Quick Smoke Test
```bash
# Verify framework is operational
cd frameworks/{language}/{framework}
make test  # or language-specific command
```

### Full Test Suite
```bash
# All frameworks
make test-all

# Specific language
make test-python
make test-typescript
make test-go
```

### With Coverage
```bash
# Generate coverage report
make test-coverage

# Results in coverage/ directory
open coverage/index.html
```

---

## Continuous Integration

All tests run automatically on:
- Pull request creation
- Commits to main branch
- Nightly builds

See `.github/workflows/unit-tests.yml` for CI configuration.

---

## Troubleshooting

### Test Failures

1. **Database connection errors**: Verify database is running
2. **Timeout errors**: Increase test timeout or optimize test
3. **Flaky tests**: Check for timing issues or shared state
4. **Coverage failures**: Add tests for uncovered code

### Performance

- Slow tests: Use database isolation, mock external calls
- Memory leaks: Check for unclosed connections
- Flaky results: Look for timing dependencies

---

## Further Reading

- [SCOPE_AND_LIMITATIONS.md](SCOPE_AND_LIMITATIONS.md) - What we test
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [docs/](docs/) - Framework-specific documentation
