"""SQL Injection Prevention Tests for Flask REST framework.

Tests verify that SQL injection attacks are prevented through parameterized queries.
All tests use psycopg3 parameterized queries which automatically prevent SQL injection.

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest
import time


@pytest.mark.security
@pytest.mark.security_injection
class TestSQLInjectionPrevention:
    """Verify SQL injection attacks are prevented through parameterized queries."""

    def test_basic_sql_injection_in_username(self, factory, db):
        """Should not execute SQL from string input - basic OR injection.

        Input: alice' OR '1'='1
        Attack Type: Basic SQL injection
        Expected: Treated as literal string, not SQL execution
        """
        # Arrange
        injection_payload = "alice' OR '1'='1"

        # Act - Create user with injection payload as username
        user = factory.create_user(injection_payload, "alice@example.com", "Alice", "Bio")

        # Query back the user
        cursor = db.cursor()
        cursor.execute(
            "SELECT username, pk_user FROM benchmark.tb_user WHERE username = %s",
            (injection_payload,)
        )
        result = cursor.fetchone()

        # Assert - Should find the user with literal injection string as username
        assert result is not None
        assert result[0] == injection_payload
        assert result[1] == user['pk_user']

    def test_union_based_injection(self, factory, db):
        """Should not execute UNION SELECT injection.

        Input: test'; UNION SELECT * FROM users; --
        Attack Type: UNION-based injection
        Expected: Treated as literal string
        """
        # Arrange
        injection_payload = "test'; UNION SELECT * FROM users; --"

        # Act
        user = factory.create_user(injection_payload, "test@example.com")

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT username FROM benchmark.tb_user WHERE username = %s",
            (injection_payload,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == injection_payload

    def test_stacked_queries_injection(self, factory, db):
        """Should not allow stacked query execution.

        Input: test'; DROP TABLE users; --
        Attack Type: Stacked queries
        Expected: Should fail or treat as literal
        """
        # Arrange
        injection_payload = "test'; DROP TABLE users; --"

        # Act & Assert - Should not delete table
        user = factory.create_user(injection_payload, "test@example.com")

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT username FROM benchmark.tb_user WHERE username = %s",
            (injection_payload,)
        )
        result = cursor.fetchone()

        # Verify table still exists and data is intact
        assert result is not None
        assert result[0] == injection_payload

        # Verify other users can still be queried (table not dropped)
        cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
        count = cursor.fetchone()[0]
        assert count >= 1

    def test_time_based_blind_injection(self, factory, db):
        """Should not allow time-based blind SQL injection.

        Input: test' AND SLEEP(5) --
        Attack Type: Time-based blind injection
        Expected: Query returns quickly (no sleep execution)
        """
        # Arrange
        injection_payload = "test' AND SLEEP(5) --"

        # Act - Should return quickly, not after 5 seconds
        start = time.time()
        user = factory.create_user(injection_payload, "test@example.com")
        duration = time.time() - start

        # Assert - Query should complete in <1 second, not 5+
        assert duration < 1.0  # Should NOT wait 5 seconds
        assert user is not None

    def test_comment_sequence_injection(self, factory, db):
        """Should handle SQL comment sequences safely.

        Input: test' -- and test' # and test' /*
        Attack Type: Comment-based injection
        Expected: Treated as literal strings
        """
        # Arrange
        payloads = [
            "test' -- comment",
            "test' # comment",
            "test' /* block comment */",
            "test\"; DROP TABLE users; --"
        ]

        # Act & Assert
        for idx, payload in enumerate(payloads):
            user = factory.create_user(payload, f"test{idx}@example.com")

            cursor = db.cursor()
            cursor.execute(
                "SELECT username FROM benchmark.tb_user WHERE username = %s",
                (payload,)
            )
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == payload

    def test_injection_in_email_field(self, factory, db):
        """Should prevent SQL injection in email field.

        Input: test@example.com' OR '1'='1
        Expected: Treated as literal email string
        """
        # Arrange
        injection_email = "test@example.com' OR '1'='1"

        # Act
        user = factory.create_user("testuser", injection_email)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT email FROM benchmark.tb_user WHERE email = %s",
            (injection_email,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == injection_email

    def test_injection_in_post_content(self, factory, db):
        """Should prevent SQL injection in post content field.

        Input: '; DROP TABLE tb_post; --
        Expected: Treated as literal content
        """
        # Arrange
        author = factory.create_user("author", "author@example.com")
        injection_content = "'; DROP TABLE tb_post; --"

        # Act
        post = factory.create_post(author["pk_user"], "Test Post", "test-inj", injection_content)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE pk_post = %s",
            (post["pk_post"],)
        )
        result = cursor.fetchone()

        # Assert - Content is stored literally
        assert result is not None
        assert result[0] == injection_content

        # Verify table still exists
        cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
        count = cursor.fetchone()[0]
        assert count >= 1

    def test_unicode_injection_attack(self, factory, db):
        """Should handle unicode-based injection attempts.

        Input: test＇ OR ＇1＇=＇1 (fullwidth quotes)
        Expected: Treated as literal string
        """
        # Arrange - Using fullwidth Unicode quotes to bypass filters
        injection_payload = "test＇ OR ＇1＇=＇1"

        # Act
        user = factory.create_user(injection_payload, "unicode@example.com")

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT username FROM benchmark.tb_user WHERE username = %s",
            (injection_payload,)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == injection_payload
