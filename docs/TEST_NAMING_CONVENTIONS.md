# Test Naming Conventions

## Overview

VelocityBench follows a consistent test naming convention to make test purposes clear and discovery easy.

---

## File Naming

### Convention

```
test_<feature>_<aspect>.py
```

or

```
<feature>_test.py
```

### Examples

**Good:**
- `test_user_creation.py` - Tests for user creation
- `test_post_queries.py` - Tests for post queries
- `test_authentication.py` - Tests for auth
- `test_n_plus_one_prevention.py` - Tests for N+1 prevention

**Avoid:**
- `test_1.py` - No meaningful name
- `unit_tests.py` - Too generic
- `temp_test.py` - Implies temporary

### Framework-Specific Tests

For framework-specific tests, include framework name:

```
frameworks/fastapi-rest/tests/
├── test_health_checks.py
├── test_graphql_queries.py
└── test_performance.py

frameworks/strawberry/tests/
├── test_health_checks.py
├── test_graphql_queries.py
└── test_performance.py
```

---

## Test Function Naming

### Convention

```python
def test_<what>_<scenario>_<expected_result>():
    pass
```

### Structure Explanation

| Part | Purpose | Example |
|------|---------|---------|
| `test_` | Pytest discovery prefix | Required |
| `<what>` | What feature is being tested | `user_creation`, `post_query`, `auth` |
| `<scenario>` | What conditions/inputs | `with_valid_data`, `with_duplicate_username`, `async` |
| `<expected>` | Expected outcome | `succeeds`, `raises_error`, `returns_list` |

### Examples

```python
# User creation tests
def test_user_creation_with_valid_data_succeeds(db, factory):
    """Create user with valid data - should succeed."""
    user = factory.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"

def test_user_creation_with_duplicate_username_raises_error(db, factory):
    """Create user with existing username - should raise error."""
    factory.create_user("alice", "alice1@example.com")
    with pytest.raises(Exception):
        factory.create_user("alice", "alice2@example.com")

def test_user_creation_with_missing_email_uses_default(db, factory):
    """Create user without email - should use default."""
    user = factory.create_user("bob", "bob")
    assert user["email"] is None or user["email"] == ""

# Query tests
def test_post_query_with_no_filters_returns_all(db):
    """Query posts without filters - should return all posts."""
    pass

def test_post_query_with_author_filter_returns_matching(db):
    """Query posts filtered by author - should return only author's posts."""
    pass

def test_post_query_with_pagination_returns_correct_offset(db):
    """Query posts with pagination - should respect offset."""
    pass

# Performance tests
def test_post_list_query_with_1000_records_completes_in_100ms(db):
    """Query post list with 1000 records - should complete within 100ms."""
    pass

def test_n_plus_one_prevention_with_dataloader_uses_single_query(db):
    """Query posts with comments using DataLoader - should batch queries."""
    pass
```

### Naming Anti-Patterns

**Avoid:**
```python
# ❌ Non-descriptive
def test_thing(db):
    pass

def test_basic(db):
    pass

def test_something_works(db):
    pass

# ❌ Assumes test will pass
def test_user_is_created_correctly(db):  # Use "succeeds" instead
    pass

# ❌ Multiple assertions tested (too broad)
def test_user_lifecycle(db):  # Split into multiple tests
    pass

# ❌ Implementation details instead of behavior
def test_insert_into_tb_user(db):  # Use "user_creation" instead
    pass

# ❌ No clear expected outcome
def test_post_update(db):  # Use "post_update_changes_title" instead
    pass
```

---

## Test Class Naming

### Convention

```python
class Test<Feature>:
    """Test suite for <feature>."""

    def test_<scenario>(self):
        pass
```

### Example

```python
class TestUserCreation:
    """Test suite for user creation functionality."""

    def test_with_valid_data_succeeds(self, db, factory):
        """User creation with valid data succeeds."""
        user = factory.create_user("alice", "alice@example.com")
        assert user["username"] == "alice"

    def test_with_duplicate_username_raises_error(self, db, factory):
        """User creation with duplicate username raises error."""
        factory.create_user("alice", "alice1@example.com")
        with pytest.raises(Exception):
            factory.create_user("alice", "alice2@example.com")

class TestPostQueries:
    """Test suite for post query functionality."""

    def test_with_no_filters_returns_all(self, db):
        pass

    def test_with_author_filter_returns_matching(self, db):
        pass
```

---

## Async Test Naming

For async tests, add `async_` prefix:

```python
@pytest.mark.asyncio
async def test_async_user_creation_succeeds(async_db):
    """Async user creation succeeds."""
    user = await async_db.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"

@pytest.mark.asyncio
async def test_async_post_query_with_dataloader_batches_queries(async_db):
    """Async post query with DataLoader batches database queries."""
    pass
```

---

## Fixture Naming

### Convention

```python
@pytest.fixture
def <entity>_fixture():
    """<Description>."""
    pass
```

### Examples

```python
@pytest.fixture
def user_fixture(db, factory):
    """Create a test user."""
    return factory.create_user("testuser", "test@example.com")

@pytest.fixture
def user_with_posts_fixture(db, factory):
    """Create a test user with 5 posts."""
    return factory.create_user_with_posts(
        username="alice",
        identifier="alice",
        email="alice@example.com",
        post_count=5
    )

@pytest.fixture
def populated_database_fixture(db, bulk_factory):
    """Populate database with 100 users."""
    return bulk_factory.create_bulk_users(count=100)
```

---

## Marker Usage

### Test Category Markers

Use markers to categorize tests:

```python
# Unit tests
@pytest.mark.unit
def test_validate_email_format(db):
    pass

# Integration tests
@pytest.mark.integration
def test_user_creation_persists_to_database(db, factory):
    pass

# Performance tests
@pytest.mark.perf
def test_large_query_completes_in_1_second(db):
    pass

# Security tests
@pytest.mark.security
def test_sql_injection_prevention(db):
    pass

# Slow tests
@pytest.mark.slow
def test_generating_1000_users_takes_less_than_5_seconds(db):
    pass
```

### Running Specific Test Categories

```bash
# Run only integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"

# Run security and performance tests
pytest -m "security or perf"
```

---

## Parametrized Test Naming

### Convention

Use `pytest.mark.parametrize` with descriptive IDs:

```python
@pytest.mark.parametrize("email,expected", [
    ("alice@example.com", True),
    ("invalid-email", False),
    ("bob@test.co.uk", True),
])
def test_email_validation_with_various_formats(email, expected):
    """Email validation handles various formats correctly."""
    assert validate_email(email) == expected
```

Or with IDs:

```python
@pytest.mark.parametrize("email,expected", [
    ("alice@example.com", True),
    ("invalid-email", False),
    ("bob@test.co.uk", True),
], ids=[
    "standard_email",
    "invalid_format",
    "country_code_tld",
])
def test_email_validation_with_various_formats(email, expected):
    """Email validation handles various formats correctly."""
    assert validate_email(email) == expected
```

---

## Framework-Specific Conventions

### GraphQL Query Tests

```python
def test_user_query_with_valid_id_returns_user(client):
    """Query user by ID returns matching user."""
    pass

def test_user_query_with_nested_posts_returns_nested_data(client):
    """Query user with posts field returns nested post data."""
    pass

def test_mutation_create_user_with_valid_input_succeeds(client):
    """Mutation create user with valid input succeeds."""
    pass
```

### REST API Tests

```python
def test_get_user_endpoint_with_valid_id_returns_200(client):
    """GET /users/{id} with valid ID returns 200."""
    pass

def test_get_user_endpoint_with_invalid_id_returns_404(client):
    """GET /users/{id} with invalid ID returns 404."""
    pass

def test_post_user_endpoint_with_valid_data_returns_201(client):
    """POST /users with valid data returns 201."""
    pass
```

---

## Documentation in Tests

Each test should have a docstring:

```python
def test_user_creation_with_valid_data_succeeds(db, factory):
    """User creation with valid data succeeds.

    Given: Valid user data
    When: User is created
    Then: User is persisted with correct values
    """
    user = factory.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
```

### Docstring Pattern

Use **Given-When-Then** format:

```python
def test_...(args):
    """Brief one-line summary.

    Given: <preconditions>
    When: <action>
    Then: <expected outcome>
    """
    pass
```

---

## Quick Reference

| Item | Pattern | Example |
|------|---------|---------|
| File | `test_<feature>.py` | `test_user_creation.py` |
| Function | `test_<what>_<scenario>_<result>` | `test_user_creation_with_duplicate_raises_error` |
| Class | `Test<Feature>` | `TestUserCreation` |
| Async | `async def test_...` | `async def test_async_create_user_succeeds` |
| Fixture | `<entity>_fixture` | `user_fixture`, `populated_db_fixture` |
| Marker | `@pytest.mark.<type>` | `@pytest.mark.integration` |
| Docstring | Given-When-Then | See example above |

---

## Benefits

Following these conventions provides:
- ✅ **Clear intent** - Test name explains what it tests
- ✅ **Easy discovery** - Find related tests quickly
- ✅ **Better debugging** - Failed test name pinpoints issue
- ✅ **Maintainability** - Future developers understand purpose
- ✅ **Documentation** - Test names serve as examples

---

## Related Documentation

- [Test Isolation Strategy](TEST_ISOLATION_STRATEGY.md) - How test data is isolated
- [Fixture Factory Guide](FIXTURE_FACTORY_GUIDE.md) - How to create test data
- [Cross-Framework Test Data](CROSS_FRAMEWORK_TEST_DATA.md) - Consistency across frameworks
