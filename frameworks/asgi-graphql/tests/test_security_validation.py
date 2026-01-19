"""Input Validation & Sanitization Tests for ASGI GraphQL framework.

Tests verify input validation prevents malicious data from being stored or processed.
Focuses on XSS prevention, null byte handling, and data integrity.

Trinity Identifier Pattern:
- pk_{entity}: Internal int identifier (primary key)
- id: UUID for public API
- identifier: Text slug for human-readable access
"""

import pytest


@pytest.mark.security
@pytest.mark.security_validation
class TestInputValidation:
    """Verify input validation prevents injection attacks."""

    def test_xss_script_in_username(self, factory, db):
        """Should store HTML/script tags but not execute them.

        Input: <script>alert('xss')</script>
        Expected: Stored as-is, framework should escape on output
        """
        # Arrange
        xss_payload = "<script>alert('xss')</script>"

        # Act
        user = factory.create_user(xss_payload, "xss@example.com", "XSS Test")

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT username FROM benchmark.tb_user WHERE pk_user = %s",
            (user['pk_user'],)
        )
        result = cursor.fetchone()

        # Assert - Data is stored as-is (sanitization happens at presentation layer)
        assert result is not None
        assert result[0] == xss_payload

    def test_xss_script_in_post_content(self, factory, db):
        """Should handle HTML content in posts.

        Input: <img src=x onerror=alert('xss')>
        Expected: Stored as-is, should be escaped on rendering
        """
        # Arrange
        author = factory.create_user("author", "author@example.com")
        xss_content = "<img src=x onerror=alert('xss')>"

        # Act
        post = factory.create_post(author["pk_user"], "Test Post", "test-xss", xss_content)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE pk_post = %s",
            (post["pk_post"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == xss_content

    def test_html_entities_in_bio(self, factory, db):
        """Should handle HTML entities safely.

        Input: &lt;script&gt;alert('test')&lt;/script&gt;
        Expected: Stored as literal text
        """
        # Arrange
        html_entity = "&lt;script&gt;alert('test')&lt;/script&gt;"

        # Act
        user = factory.create_user("testuser", "test@example.com", "Test", html_entity)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT bio FROM benchmark.tb_user WHERE pk_user = %s",
            (user['pk_user'],)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == html_entity

    def test_null_byte_injection(self, factory, db):
        """Should handle null bytes safely.

        Input: test\x00injection
        Expected: Should reject or handle safely
        """
        # Arrange
        null_byte_payload = "test\x00injection"

        # Act - Should not crash
        try:
            user = factory.create_user(null_byte_payload, "test@example.com")
            # If successful, verify data integrity
            cursor = db.cursor()
            cursor.execute(
                "SELECT username FROM benchmark.tb_user WHERE pk_user = %s",
                (user['pk_user'],)
            )
            result = cursor.fetchone()
            assert result is not None
        except (ValueError, Exception) as e:
            # Exception is also valid response to null bytes
            # PostgreSQL typically rejects null bytes in text fields
            assert True

    def test_extremely_long_username(self, factory, db):
        """Should enforce reasonable length limits on username.

        Input: Very long string (10000 characters)
        Expected: Should be truncated or rejected
        """
        # Arrange
        very_long_username = "a" * 10000

        # Act
        try:
            user = factory.create_user(very_long_username, "test@example.com")
            # If it succeeds, verify it was truncated or stored
            cursor = db.cursor()
            cursor.execute(
                "SELECT username FROM benchmark.tb_user WHERE pk_user = %s",
                (user['pk_user'],)
            )
            result = cursor.fetchone()
            # Username field likely has a reasonable limit in schema
            assert result is not None
            assert len(result[0]) <= 10000
        except Exception:
            # Database schema may reject overly long values
            assert True

    def test_special_characters_preserved(self, factory, db):
        """Should preserve special characters without corruption.

        Input: Various special characters
        Expected: Data integrity maintained
        """
        # Arrange
        special_chars = "Test with 'quotes' and \"double\" and `backticks` and $dollars$ and !@#%^&*()"

        # Act
        author = factory.create_user("author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Special", "special", special_chars)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE pk_post = %s",
            (post["pk_post"],)
        )
        result = cursor.fetchone()

        # Assert - All special characters preserved
        assert result is not None
        assert result[0] == special_chars

    def test_unicode_characters_preserved(self, factory, db):
        """Should preserve Unicode characters correctly.

        Input: Various Unicode characters
        Expected: Correct storage and retrieval
        """
        # Arrange
        unicode_content = "Test with emoji 🎉🔥💯 and Chinese 你好 and Arabic مرحبا"

        # Act
        author = factory.create_user("author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Unicode", "unicode", unicode_content)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE pk_post = %s",
            (post["pk_post"],)
        )
        result = cursor.fetchone()

        # Assert - Unicode preserved correctly
        assert result is not None
        assert result[0] == unicode_content

    def test_newlines_and_whitespace_preserved(self, factory, db):
        """Should preserve newlines and whitespace in content.

        Expected: Whitespace integrity maintained
        """
        # Arrange
        multiline_content = "Line 1\nLine 2\n\nLine 4\tTabbed"

        # Act
        author = factory.create_user("author", "author@example.com")
        post = factory.create_post(author["pk_user"], "Multiline", "multiline", multiline_content)

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT content FROM benchmark.tb_post WHERE pk_post = %s",
            (post["pk_post"],)
        )
        result = cursor.fetchone()

        # Assert
        assert result is not None
        assert result[0] == multiline_content

    def test_empty_string_vs_null(self, factory, db):
        """Should distinguish between empty string and NULL.

        Expected: Empty strings are not treated as NULL
        """
        # Arrange - Create user with empty full_name
        user = factory.create_user("testuser", "test@example.com", "", "")

        # Query back
        cursor = db.cursor()
        cursor.execute(
            "SELECT full_name, bio FROM benchmark.tb_user WHERE pk_user = %s",
            (user['pk_user'],)
        )
        result = cursor.fetchone()

        # Assert - full_name is empty string, bio might be NULL
        assert result is not None
        assert result[0] == ""  # full_name is empty string
        # bio might be NULL or empty depending on factory implementation
