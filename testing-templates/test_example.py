"""Example unit and integration tests for VelocityBench.

This template shows the standard pattern for testing:
1. UNIT TESTS: Test functions/classes without database
2. INTEGRATION TESTS: Test with database using fixtures
"""

import pytest
from typing import Dict, Any


# ============================================================================
# Unit Tests (no database dependency)
# ============================================================================

@pytest.mark.unit
class TestUserValidation:
    """Unit tests for user validation logic."""

    def test_email_validation_valid(self):
        """Valid email should pass validation."""
        from validators import is_valid_email
        assert is_valid_email("user@example.com") is True

    def test_email_validation_invalid(self):
        """Invalid email should fail validation."""
        from validators import is_valid_email
        assert is_valid_email("invalid-email") is False

    def test_name_normalization(self):
        """Name should be normalized correctly."""
        from validators import normalize_name
        assert normalize_name("JOHN DOE") == "john doe"
        assert normalize_name("  alice  ") == "alice"

    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", True),
        ("invalid@", False),
        ("no-at-sign.com", False),
        ("spaces @example.com", False),
    ])
    def test_email_validation_parametrized(self, email, expected):
        """Test multiple email formats."""
        from validators import is_valid_email
        assert is_valid_email(email) == expected


@pytest.mark.unit
class TestDataTransformation:
    """Unit tests for data transformation functions."""

    def test_user_dict_to_object(self):
        """Convert user dict to object."""
        from models import User
        user_dict = {"id": 1, "name": "Alice", "email": "alice@example.com"}
        user = User(**user_dict)
        assert user.id == 1
        assert user.name == "Alice"
        assert user.email == "alice@example.com"

    def test_product_price_formatting(self):
        """Product price should be formatted correctly."""
        from formatters import format_price
        assert format_price(19.99) == "$19.99"
        assert format_price(100.00) == "$100.00"
        assert format_price(0.50) == "$0.50"


# ============================================================================
# Integration Tests (with database)
# ============================================================================

@pytest.mark.integration
class TestUserQueries:
    """Integration tests for user queries with database."""

    def test_create_user(self, db, factory):
        """Test creating a user in database."""
        # Arrange
        user_data = factory.create_user("Alice", "alice@example.com")

        # Assert
        assert user_data is not None
        assert user_data["name"] == "Alice"
        assert user_data["email"] == "alice@example.com"
        assert user_data["id"] is not None

    def test_get_user_by_id(self, db, factory):
        """Test retrieving a user by ID."""
        # Arrange
        created = factory.create_user("Bob", "bob@example.com")
        user_id = created["id"]

        # Act
        cursor = db.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        user = dict(cursor.fetchone())

        # Assert
        assert user["id"] == user_id
        assert user["name"] == "Bob"
        assert user["email"] == "bob@example.com"

    def test_list_users(self, db, factory):
        """Test listing all users."""
        # Arrange
        factory.create_user("Alice", "alice@example.com")
        factory.create_user("Bob", "bob@example.com")
        factory.create_user("Charlie", "charlie@example.com")

        # Act
        cursor = db.execute("SELECT id, name, email FROM users ORDER BY name")
        users = [dict(row) for row in cursor.fetchall()]

        # Assert
        assert len(users) == 3
        assert users[0]["name"] == "Alice"
        assert users[1]["name"] == "Bob"
        assert users[2]["name"] == "Charlie"

    def test_update_user(self, db, factory):
        """Test updating a user."""
        # Arrange
        created = factory.create_user("Alice", "alice@example.com")
        user_id = created["id"]

        # Act
        db.execute(
            "UPDATE users SET email = %s WHERE id = %s",
            ("alice.new@example.com", user_id),
        )
        db.connection.commit()

        # Assert
        cursor = db.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        updated = dict(cursor.fetchone())
        assert updated["email"] == "alice.new@example.com"

    def test_delete_user(self, db, factory):
        """Test deleting a user."""
        # Arrange
        created = factory.create_user("Alice", "alice@example.com")
        user_id = created["id"]

        # Act
        db.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.connection.commit()

        # Assert
        cursor = db.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        assert result is None


@pytest.mark.integration
class TestProductQueries:
    """Integration tests for product queries."""

    def test_create_product(self, db, factory):
        """Test creating a product."""
        # Arrange
        company = factory.create_company("ACME Corp")

        # Act
        product = factory.create_product("Widget", 19.99, company["id"])

        # Assert
        assert product is not None
        assert product["name"] == "Widget"
        assert product["price"] == 19.99

    def test_list_products_by_company(self, db, factory):
        """Test listing products for a company."""
        # Arrange
        company1 = factory.create_company("ACME Corp")
        company2 = factory.create_company("TechCorp")

        factory.create_product("Widget A", 10.0, company1["id"])
        factory.create_product("Widget B", 20.0, company1["id"])
        factory.create_product("Gadget", 30.0, company2["id"])

        # Act
        cursor = db.execute(
            "SELECT id, name, price FROM products WHERE company_id = %s ORDER BY name",
            (company1["id"],),
        )
        products = [dict(row) for row in cursor.fetchall()]

        # Assert
        assert len(products) == 2
        assert products[0]["name"] == "Widget A"
        assert products[1]["name"] == "Widget B"


@pytest.mark.integration
@pytest.mark.slow
class TestComplexQueries:
    """Integration tests for more complex queries."""

    def test_user_with_orders(self, db, factory):
        """Test retrieving user with order count."""
        # Arrange
        user = factory.create_user("Alice", "alice@example.com")

        # Create some orders
        cursor = db.execute(
            "INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id",
            (user["id"], 100.0),
        )
        db.connection.commit()

        # Act
        cursor = db.execute(
            "SELECT u.id, u.name, COUNT(o.id) as order_count "
            "FROM users u "
            "LEFT JOIN orders o ON u.id = o.user_id "
            "WHERE u.id = %s "
            "GROUP BY u.id",
            (user["id"],),
        )
        result = dict(cursor.fetchone())

        # Assert
        assert result["order_count"] == 1


# ============================================================================
# Test Fixtures / Helpers
# ============================================================================

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
    }


@pytest.fixture
def sample_product_data() -> Dict[str, Any]:
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "price": 19.99,
        "description": "A test product",
    }
