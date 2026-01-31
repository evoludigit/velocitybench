# Test Isolation Strategy

## Overview

VelocityBench uses **transaction-based test isolation** to ensure clean data between test runs. Each test executes in its own PostgreSQL transaction that is automatically rolled back after completion, preventing data leakage between tests.

This guide explains how test isolation works and how to write tests that respect this pattern.

---

## How It Works

### The Isolation Pattern

All tests use the `db` fixture from `tests/common/fixtures.py`:

```python
@pytest.fixture
def db():
    """Provide a database connection with automatic transaction rollback."""
    conn = psycopg.connect(...)
    conn.autocommit = False

    # Clean up before test
    with conn.cursor() as cursor:
        cursor.execute("TRUNCATE benchmark.tb_comment CASCADE")
        cursor.execute("TRUNCATE benchmark.tb_post CASCADE")
        cursor.execute("TRUNCATE benchmark.tb_user CASCADE")
    conn.commit()

    # Run test in transaction - automatically rolls back
    try:
        with conn.transaction():
            yield conn
    finally:
        conn.close()
```

### Execution Flow

```
Test Setup
    ↓
TRUNCATE all benchmark tables
    ↓
BEGIN TRANSACTION
    ↓
RUN TEST
    ↓
[Test inserts/updates data]
    ↓
ROLLBACK TRANSACTION (automatic)
    ↓
Next test starts with clean data
```

### Why This Approach?

**Advantages:**
- ✅ **No Manual Cleanup** - Tests don't need cleanup code
- ✅ **Clean Between Tests** - No data carries over to next test
- ✅ **Fast** - Rollback is faster than deleting records
- ✅ **Concurrent Safe** - Each test sees isolated view
- ✅ **Consistent** - Pre-test TRUNCATE removes any residual data

**Trade-offs:**
- ⚠️ **Cannot test transactions** - Tests run inside transaction (see workarounds below)
- ⚠️ **Read-only on some data** - Foreign keys must exist before test inserts
- ⚠️ **Sequence management** - Must account for auto-increment sequences

---

## Writing Tests with Isolation

### Basic Test Pattern

```python
import pytest

@pytest.mark.integration
def test_user_creation(db):
    """Test that users can be created."""
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO benchmark.tb_user (username, email, full_name) "
            "VALUES (%s, %s, %s) "
            "RETURNING pk_user, id, username",
            ("testuser", "test@example.com", "Test User"),
        )
        row = cursor.fetchone()
        pk_user, user_id, username = row

        assert pk_user is not None
        assert user_id is not None
        assert username == "testuser"
```

**Key Points:**
- Each test gets a fresh `db` connection
- Data inserted in test is automatically rolled back
- No need to delete test data
- No teardown code required

### Using the Factory Fixture

```python
import pytest
from tests.common.factory import factory

@pytest.mark.integration
def test_post_creation_with_author(db, factory):
    """Test creating a post with an author."""
    # factory depends on db, so use both
    user = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(
        fk_author=user["pk_user"],
        title="My First Post",
        content="Hello world!"
    )

    assert post["title"] == "My First Post"
    assert post["fk_author"] == user["pk_user"]
```

### Using Bulk Factory

```python
import pytest
from tests.common.bulk_factory import bulk_factory

@pytest.mark.perf
def test_query_performance_with_100_users(db, bulk_factory):
    """Test query performance with realistic data volume."""
    users = bulk_factory.create_bulk_users(count=100, prefix="user")

    # Create posts for each user
    with db.cursor() as cursor:
        for user in users:
            for post_num in range(5):
                cursor.execute(
                    "INSERT INTO benchmark.tb_post (fk_author, title) "
                    "VALUES (%s, %s)",
                    (user["pk_user"], f"Post {post_num} by {user['username']}"),
                )

    # Test query performance on realistic dataset
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
        count = cursor.fetchone()[0]
        assert count == 500  # 100 users × 5 posts
```

---

## Advanced Patterns

### Testing Transactions (Workaround)

Since tests run inside a transaction, you cannot test transaction behavior directly. For testing transactions:

```python
@pytest.mark.integration
def test_transaction_isolation():
    """Test transaction isolation using separate connections."""
    import psycopg

    conn1 = psycopg.connect(...)
    conn2 = psycopg.connect(...)

    try:
        # Conn1: Insert and don't commit
        with conn1.cursor() as cur:
            cur.execute("INSERT INTO benchmark.tb_user ...")
            # Don't commit yet

            # Conn2: Shouldn't see uncommitted data
            with conn2.cursor() as cur2:
                cur2.execute("SELECT COUNT(*) FROM benchmark.tb_user")
                count = cur2.fetchone()[0]
                assert count == 0  # Isolation works!

        # Rollback explicit transaction
        conn1.rollback()
    finally:
        conn1.close()
        conn2.close()
```

### Testing Constraint Violations

```python
@pytest.mark.integration
def test_foreign_key_violation(db):
    """Test that FK constraints are enforced."""
    with db.cursor() as cursor:
        with pytest.raises(Exception):  # psycopg.errors.ForeignKeyViolation
            cursor.execute(
                "INSERT INTO benchmark.tb_post (fk_author, title) "
                "VALUES (%s, %s)",
                (999999, "Orphaned Post"),  # Non-existent user
            )
```

### Testing with Fixtures in Different States

```python
@pytest.mark.integration
def test_querying_populated_database(db, bulk_factory):
    """Test queries work correctly with pre-populated data."""
    # Setup: Create realistic data
    users = bulk_factory.create_bulk_users(count=10)
    posts = bulk_factory.create_user_with_posts(
        username="alice",
        identifier="alice",
        email="alice@example.com",
        post_count=20
    )

    # Test: Query the data
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = %s",
            (posts["user"]["pk_user"],),
        )
        count = cursor.fetchone()[0]
        assert count == 20
```

---

## Sequence Management

PostgreSQL sequences continue to increment even after transaction rollback. This is by design:

```python
def test_sequence_increment(db, factory):
    """Sequence increments are not rolled back."""
    user1 = factory.create_user("alice", "alice@example.com")
    pk1 = user1["pk_user"]
    # Transaction rolls back

    # New test
    user2 = factory.create_user("bob", "bob@example.com")
    pk2 = user2["pk_user"]

    # PKs will not be consecutive due to rollback!
    # user1.pk_user might be 1
    # user2.pk_user might be 3 (not 2)
    assert pk2 > pk1  # True, but not necessarily pk1 + 1
```

**Best Practice:** Don't rely on specific primary key values. Use the returned PKs from factory methods instead.

---

## Debugging Test Failures

### Viewing Data State During Test

Use pytest's interactive debugging with `-s` flag:

```bash
pytest tests/test_users.py::test_user_creation -s
```

Or add print statements:

```python
def test_something(db):
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO benchmark.tb_user ...")

        # Check state
        cursor.execute("SELECT * FROM benchmark.tb_user")
        rows = cursor.fetchall()
        print(f"Current users: {rows}")  # Shows with -s flag
```

### Capturing State Before Rollback

```python
def test_with_state_capture(db, factory):
    """Capture state before rollback."""
    user = factory.create_user("alice", "alice@example.com")

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM benchmark.tb_user WHERE pk_user = %s", (user["pk_user"],))
        row = cursor.fetchone()
        print(f"User state: {row}")  # -s flag shows this

        assert row is not None

    # This point: transaction rolls back (automatic)
```

### Viewing Logs

Use `--log-cli-level=DEBUG` to see database operations:

```bash
pytest tests/ --log-cli-level=DEBUG
```

---

## Isolation Levels

By default, tests use PostgreSQL's **READ COMMITTED** isolation level (connection default). For specific testing needs:

```python
@pytest.mark.integration
def test_serializable_isolation(db):
    """Test with SERIALIZABLE isolation level."""
    with db.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cursor.execute("INSERT INTO benchmark.tb_user ...")
```

**Common Isolation Levels for Testing:**
- `READ UNCOMMITTED` - Lowest isolation (rarely used for testing)
- `READ COMMITTED` - Default, good for most tests
- `REPEATABLE READ` - Stronger consistency
- `SERIALIZABLE` - Strictest, use for transaction testing

---

## Cleanup Issues

### Problem: Data from Previous Test Run

If a test fails and doesn't roll back properly:

```bash
# Hard reset - truncate all tables
psql -U benchmark -d velocitybench_benchmark -c "
TRUNCATE benchmark.tb_comment CASCADE;
TRUNCATE benchmark.tb_post CASCADE;
TRUNCATE benchmark.tb_user CASCADE;
"
```

Or drop and recreate:

```bash
docker-compose exec postgres psql -U benchmark -c "DROP SCHEMA benchmark CASCADE; CREATE SCHEMA benchmark;"
```

### Problem: Foreign Key Constraint Violations

If you see FK violations during test cleanup:

```python
# In your test - ensure parent exists before child
user = factory.create_user("alice", "alice@example.com")
post = factory.create_post(fk_author=user["pk_user"], title="Post")
```

The `TRUNCATE ... CASCADE` in the fixture handles this automatically.

---

## Best Practices

### ✅ DO:

- **Use the `db` fixture** - Ensures transaction isolation
- **Use `factory` for test data** - Consistent, maintainable test setup
- **Group related tests with markers** - `@pytest.mark.integration`, `@pytest.mark.perf`
- **Name tests descriptively** - `test_<what>_<scenario>_<expected>`
- **Keep tests independent** - No test should depend on another test's data

### ❌ DON'T:

- **Don't commit in tests** - Transaction handles this automatically
- **Don't rely on specific PKs** - Sequences don't reset on rollback
- **Don't expect data to persist** - Everything rolls back after test
- **Don't share test data** - Use fixtures for isolation
- **Don't test transactions directly** - Use separate connections (see workarounds)

---

## Troubleshooting Checklist

| Problem | Cause | Solution |
|---------|-------|----------|
| Test sees data from another test | Fixture not applied | Add `db` parameter to test |
| FK constraint violation | Parent entity missing | Use factory to create parent first |
| Data persists after test | Manual commit or wrong fixture | Don't commit; use `db` fixture |
| PK values aren't sequential | Sequence not reset on rollback | Don't rely on specific PKs |
| Test hangs on connection | Deadlock or transaction conflict | Check for explicit transactions |
| Database connection timeout | DB not running | `make db-up` or `docker-compose up postgres` |

---

## Related Documentation

- [Test Naming Conventions](TEST_NAMING_CONVENTIONS.md) - How to name tests
- [Fixture Factory Guide](FIXTURE_FACTORY_GUIDE.md) - How to use factory.py
- [Performance Baseline Management](PERFORMANCE_BASELINE_MANAGEMENT.md) - Comparing test runs
- [Cross-Framework Test Data](CROSS_FRAMEWORK_TEST_DATA.md) - Consistency across frameworks

---

## Summary

VelocityBench's transaction-based isolation strategy provides:
- ✅ Clean data between tests (no manual cleanup)
- ✅ Fast test execution (rollback is quick)
- ✅ Reliable test independence (isolation guaranteed)
- ✅ Realistic query testing (normal transaction semantics)

By understanding and following this pattern, you can write confident, maintainable tests that provide genuine coverage.
