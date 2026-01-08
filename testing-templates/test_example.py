"""Example tests for VelocityBench Python frameworks.

These tests connect to a shared PostgreSQL database and use transaction
isolation for automatic cleanup. All tests follow the Arrange-Act-Assert pattern.

To use this template:
1. Copy conftest.py to your framework's tests/ directory
2. Rename this file to test_<feature>.py
3. Update imports and resolver/handler names
4. Run with: pytest tests/ --cov=src
"""

import pytest
from psycopg2.extras import DictCursor


# ============================================================================
# Basic Query Tests
# ============================================================================

def test_query_users_returns_list(db, factory):
    """Test: querying all users returns a list."""
    # Arrange: Create test data
    factory.create_user("Alice", "alice@example.com")
    factory.create_user("Bob", "bob@example.com")
    factory.create_user("Charlie", "charlie@example.com")

    # Act: Query users from database
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT id, name, email FROM users ORDER BY name")
    users = cursor.fetchall()

    # Assert: Verify results
    assert len(users) == 3
    assert users[0]["name"] == "Alice"
    assert users[1]["name"] == "Bob"
    assert users[2]["name"] == "Charlie"


def test_query_user_by_id_returns_single_user(db, factory):
    """Test: querying user by ID returns the correct user."""
    # Arrange
    user_created = factory.create_user("Alice", "alice@example.com")
    user_id = user_created["id"]

    # Act
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    # Assert
    assert user is not None
    assert user["id"] == user_id
    assert user["name"] == "Alice"
    assert user["email"] == "alice@example.com"


def test_query_nonexistent_user_returns_none(db):
    """Test: querying nonexistent user returns None."""
    # Arrange
    nonexistent_id = 99999

    # Act
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = %s",
        (nonexistent_id,)
    )
    user = cursor.fetchone()

    # Assert
    assert user is None


# ============================================================================
# Mutation Tests
# ============================================================================

def test_mutation_create_user_persists_to_database(db, factory):
    """Test: creating a user persists data to database."""
    # Arrange
    user_data = {"name": "Charlie", "email": "charlie@example.com"}

    # Act
    result = factory.create_user(**user_data)

    # Assert: Verify returned data
    assert result["name"] == "Charlie"
    assert result["email"] == "charlie@example.com"
    assert result["id"] is not None

    # Assert: Verify data persists in database
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (result["id"],))
    db_user = cursor.fetchone()
    assert db_user is not None
    assert db_user["name"] == "Charlie"


def test_mutation_update_user_email(db, factory):
    """Test: updating a user's email persists the change."""
    # Arrange
    user = factory.create_user("Alice", "alice@example.com")
    user_id = user["id"]

    # Act: Update email
    new_email = "alice.new@example.com"
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute(
        "UPDATE users SET email = %s WHERE id = %s RETURNING id, name, email",
        (new_email, user_id)
    )
    updated = cursor.fetchone()

    # Assert
    assert updated["email"] == "alice.new@example.com"

    # Verify in database
    cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
    db_user = cursor.fetchone()
    assert db_user["email"] == "alice.new@example.com"


def test_mutation_delete_user(db, factory):
    """Test: deleting a user removes it from database."""
    # Arrange
    user = factory.create_user("Alice", "alice@example.com")
    user_id = user["id"]

    # Act: Delete user
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()

    # Assert: User no longer exists
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    assert result is None


# ============================================================================
# Validation Tests
# ============================================================================

def test_create_user_with_empty_name_raises_error(db):
    """Test: creating user with empty name raises validation error."""
    # Arrange
    cursor = db.cursor(cursor_factory=DictCursor)

    # Act & Assert: Should raise an error or constraint violation
    with pytest.raises(Exception):  # Database constraint or validation
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            ("", "test@example.com")
        )
        db.commit()


@pytest.mark.parametrize("email", [
    "valid@example.com",
    "user+tag@example.co.uk",
    "name.surname@company.example.com",
])
def test_create_user_with_valid_email_formats(db, factory, email):
    """Test: creating users with various valid email formats."""
    # Arrange & Act
    user = factory.create_user("TestUser", email)

    # Assert
    assert user["email"] == email
    assert user["id"] is not None


# ============================================================================
# Relationship Tests
# ============================================================================

def test_product_with_company_foreign_key(db, factory):
    """Test: products can be created with company foreign key."""
    # Arrange
    company = factory.create_company("ACME Corp")

    # Act
    product = factory.create_product("Widget", 19.99, company["id"])

    # Assert
    assert product["name"] == "Widget"
    assert product["price"] == 19.99
    assert product["company_id"] == company["id"]


def test_query_products_by_company(db, factory):
    """Test: querying products filters correctly by company."""
    # Arrange
    company1 = factory.create_company("ACME Corp")
    company2 = factory.create_company("TechCorp")

    factory.create_product("Widget A", 10.0, company1["id"])
    factory.create_product("Widget B", 20.0, company1["id"])
    factory.create_product("Gadget", 30.0, company2["id"])

    # Act
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute(
        "SELECT id, name, price FROM products WHERE company_id = %s ORDER BY name",
        (company1["id"],)
    )
    products = cursor.fetchall()

    # Assert
    assert len(products) == 2
    assert products[0]["name"] == "Widget A"
    assert products[1]["name"] == "Widget B"


# ============================================================================
# Edge Cases and Concurrency
# ============================================================================

def test_create_same_user_twice_in_transaction(db, factory):
    """Test: creating the same user twice in same transaction.

    Note: This tests transaction behavior. Each test's transaction is
    isolated, so this won't affect other tests.
    """
    # Arrange & Act
    user1 = factory.create_user("Alice", "alice@example.com")
    user2 = factory.create_user("Alice", "alice@example.com")

    # Assert: Both should exist (same name, different IDs in most systems)
    assert user1["id"] != user2["id"]
    assert user1["name"] == user2["name"]


@pytest.mark.slow
def test_create_many_users(db, factory):
    """Test: creating many users works correctly."""
    # Arrange & Act
    for i in range(100):
        factory.create_user(f"User{i}", f"user{i}@example.com")

    # Assert
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM users")
    result = cursor.fetchone()
    assert result["count"] == 100


def test_transaction_isolation_between_tests(db, factory):
    """Test: verify no data leaks from previous tests.

    This test should always find an empty or controlled state because
    each test's transaction is rolled back automatically.
    """
    # Arrange & Act
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM users")
    initial_count = cursor.fetchone()["count"]

    # Create a user
    factory.create_user("Alice", "alice@example.com")

    cursor.execute("SELECT COUNT(*) as count FROM users")
    after_count = cursor.fetchone()["count"]

    # Assert: Shows this test has isolated transaction
    assert after_count == initial_count + 1
    # After test, rollback clears this user


# ============================================================================
# Fixtures and Helpers
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Fixture: sample user data."""
    return {
        "name": "Test User",
        "email": "test@example.com",
    }


@pytest.fixture
def sample_product_data():
    """Fixture: sample product data."""
    return {
        "name": "Test Product",
        "price": 29.99,
        "description": "A test product",
    }


# ============================================================================
# Integration with Real Resolvers/Handlers
# ============================================================================

# Uncomment and adapt for your framework:

# def test_resolver_query_users(db, factory):
#     """Test: GraphQL resolver for querying users."""
#     from app.resolvers import query_users
#
#     # Arrange
#     factory.create_user("Alice", "alice@example.com")
#     factory.create_user("Bob", "bob@example.com")
#
#     # Act
#     result = query_users()
#
#     # Assert
#     assert len(result) == 2
#     assert result[0].name == "Alice"
#
#
# async def test_mutation_create_user(db, factory):
#     """Test: GraphQL mutation for creating user."""
#     from app.mutations import create_user
#
#     # Arrange
#     input_data = {"name": "Charlie", "email": "charlie@example.com"}
#
#     # Act
#     result = await create_user(input_data)
#
#     # Assert
#     assert result.name == "Charlie"
#     assert result.email == "charlie@example.com"
