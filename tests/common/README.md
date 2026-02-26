# Shared Test Infrastructure

This directory contains shared test fixtures, factories, and utilities used across all VelocityBench framework test suites.

## Purpose

Consolidates duplicated test code across 6 frameworks (Strawberry, Graphene, FastAPI, Flask, Ariadne, ASGI-GraphQL) into a single source of truth, reducing maintenance burden by ~75%.

## Modules

### `fixtures.py` - Database Connection & Configuration

**Provides:**
- `db` fixture: Database connection with transaction isolation
- `pytest_configure`: Registers custom pytest markers
- Database configuration from environment variables

**Environment Variables:**
- `DB_HOST` - PostgreSQL host (default: `localhost`)
- `DB_PORT` - PostgreSQL port (default: `5434`)
- `DB_USER` - PostgreSQL user (default: `benchmark`)
- `DB_PASSWORD` - PostgreSQL password (default: `benchmark123`)
- `DB_NAME` - PostgreSQL database (default: `velocitybench_benchmark`)

**Markers Registered:**
- `slow`, `security`, `security_injection`, `security_validation`, `security_integrity`
- `integration`, `mutation`, `error`, `query`, `relationship`, `schema`, `boundary`
- `perf`, `perf_queries`

### `factory.py` - Test Data Factory

**Provides:**
- `factory` fixture: Creates test data using the Trinity Identifier Pattern

**Methods:**
- `create_user(username, email_or_identifier=None, email=None, full_name=None, bio=None) -> dict`
- `create_post(fk_author, title, identifier=None, content=None) -> dict`
- `create_comment(fk_post, fk_author, identifier, content) -> dict`

**Trinity Identifier Pattern:**
- `pk_{entity}`: Internal integer primary key
- `id`: UUID for public API
- `identifier`: Human-readable text slug

### `bulk_factory.py` - Bulk Operations Factory

**Provides:**
- `bulk_factory` fixture: Efficient bulk test data operations

**Methods:**
- `create_bulk_users(count, prefix="user") -> list[dict]` - Create multiple users
- `create_user_with_posts(username, identifier, email, post_count=5) -> dict` - User with posts
- `create_post_with_comments(author_pk, title, identifier, comment_count=3) -> dict` - Post with comments
- `cleanup_all_data() -> None` - Truncate all benchmark tables
- `get_user_count() -> int` - Count users
- `get_post_count(author_pk=None) -> int` - Count posts
- `get_comment_count(post_pk=None) -> int` - Count comments

## Usage in Frameworks

Each framework's `conftest.py` imports these fixtures via pytest's plugin system:

```python
# frameworks/{framework}/tests/conftest.py
pytest_plugins = [
    "tests.common.fixtures",
    "tests.common.factory",
    "tests.common.bulk_factory",
]
```

This automatically registers all fixtures in that framework's test suite.

## Using Fixtures in Tests

### Simple Test with Factory

```python
def test_create_user(factory):
    """Test user creation."""
    user = factory.create_user("testuser", "test@example.com")

    assert user['username'] == "testuser"
    assert user['email'] == "test@example.com"
    assert user['pk_user'] > 0
```

### Bulk Operations

```python
def test_bulk_operations(bulk_factory):
    """Test bulk user creation."""
    users = bulk_factory.create_bulk_users(100, prefix="bulk")

    assert len(users) == 100
    assert bulk_factory.get_user_count() == 100
```

### Cleanup

```python
def test_with_cleanup(bulk_factory):
    """Test with explicit cleanup."""
    bulk_factory.create_bulk_users(50)

    # Test runs...

    bulk_factory.cleanup_all_data()
    assert bulk_factory.get_user_count() == 0
```

## Database Isolation

Each test:
1. Receives an isolated database connection
2. Runs in a transaction with `REPEATABLE READ` isolation
3. All tables are truncated before the test starts
4. Transaction automatically rolls back after the test

This ensures test data doesn't leak between tests.

## Adding New Shared Fixtures

To add a fixture that's needed by multiple frameworks:

1. Add it to the appropriate module (`fixtures.py`, `factory.py`, `bulk_factory.py`)
2. Import it via `pytest_plugins` in each framework's `conftest.py`
3. Update this README

Example:

```python
# tests/common/fixtures.py
@pytest.fixture
def my_new_fixture(db):
    """Description of fixture."""
    # Implementation
    yield something
```

All frameworks automatically get this fixture without code changes.

## Framework-Specific Overrides

If a framework needs to override a fixture behavior:

```python
# frameworks/{framework}/tests/conftest.py
pytest_plugins = [
    "tests.common.fixtures",
    "tests.common.factory",
    "tests.common.bulk_factory",
]

# Override db fixture if needed
@pytest.fixture
def db():
    # Custom implementation for this framework
    pass
```

The framework's definition takes precedence over the shared one.

## Testing Shared Fixtures

Run tests for a single framework to verify shared fixtures work:

```bash
cd frameworks/strawberry
pytest tests/ -v
```

All 6 frameworks should have identical fixture behavior.

## Historical Migration

This consolidation reduced:
- **Lines of duplicated code**: 12,514 → ~1,500 (88% reduction)
- **Files with fixture definitions**: 6 → 1
- **Maintenance burden**: 6× → 1×

Extracted from:
- `frameworks/strawberry/tests/conftest.py` (452 lines)
- `frameworks/graphene/tests/conftest.py` (212 lines)
- `frameworks/fastapi-rest/tests/conftest.py` (212 lines)
- `frameworks/flask-rest/tests/conftest.py` (212 lines)
- `frameworks/ariadne/tests/conftest.py` (173 lines)
- `frameworks/asgi-graphql/tests/conftest.py` (173 lines)

**Total extracted: 1,434 lines into shared infrastructure**

## Verification

To verify all frameworks use the shared infrastructure:

```bash
# Should show identical output for all frameworks
for dir in frameworks/*/tests; do
    echo "=== $dir ==="
    grep -l "pytest_plugins" "$dir/conftest.py"
done
```

To check fixture discovery:

```bash
cd frameworks/strawberry
pytest --fixtures | grep -E "db|factory|bulk_factory"
```
