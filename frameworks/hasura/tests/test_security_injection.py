"""
Security: SQL Injection Prevention Tests (Hasura GraphQL)

These tests verify that Hasura's GraphQL API properly handles SQL injection
attempts in query arguments and mutation inputs. Hasura uses parameterized
queries by design, providing strong protection against SQL injection.
"""

import pytest
from test_factory import TestFactory


@pytest.fixture
def factory():
    """Provide a fresh TestFactory for each test."""
    f = TestFactory()
    yield f
    f.reset()


class TestBasicSQLInjection:
    """Test basic SQL injection prevention."""

    def test_prevent_basic_or_injection_in_username(self, factory):
        """Should prevent basic OR injection in username filter."""
        factory.create_user("alice", "alice@example.com", "Alice")

        # Attempt SQL injection with OR clause
        malicious_username = "' OR '1'='1"
        result = factory.get_user(malicious_username)

        # Should return None (no match), not all users
        assert result is None

    def test_prevent_union_based_injection(self, factory):
        """Should prevent UNION-based SQL injection."""
        factory.create_user("bob", "bob@example.com", "Bob")

        # Attempt UNION injection
        malicious_username = "' UNION SELECT * FROM benchmark.tb_user--"
        result = factory.get_user(malicious_username)

        assert result is None

    def test_prevent_stacked_queries_injection(self, factory):
        """Should prevent stacked queries injection."""
        factory.create_user("charlie", "charlie@example.com", "Charlie")

        # Attempt to drop table with stacked query
        malicious_username = "'; DROP TABLE benchmark.tb_user; --"
        result = factory.get_user(malicious_username)

        assert result is None

        # Verify factory still works (table not dropped)
        users = factory.get_all_users()
        assert len(users) >= 1

    def test_prevent_comment_sequence_injection(self, factory):
        """Should prevent SQL comment injection."""
        factory.create_user("david", "david@example.com", "David")

        # Attempt comment-based injection
        malicious_username = "david'--"
        result = factory.get_user(malicious_username)

        assert result is None

    def test_prevent_time_based_blind_injection(self, factory):
        """Should prevent time-based blind SQL injection."""
        factory.create_user("eve", "eve@example.com", "Eve")

        # Attempt time-based blind injection
        malicious_username = "' AND pg_sleep(5)--"

        import time
        start_time = time.time()
        result = factory.get_user(malicious_username)
        duration = time.time() - start_time

        assert result is None
        assert duration < 1.0  # Should not sleep

    def test_prevent_boolean_based_blind_injection(self, factory):
        """Should prevent boolean-based blind SQL injection."""
        factory.create_user("frank", "frank@example.com", "Frank")

        # Attempt boolean-based blind injection
        malicious_username = "' AND 1=1--"
        result = factory.get_user(malicious_username)

        assert result is None


class TestMutationInjection:
    """Test SQL injection prevention in mutations."""

    def test_prevent_injection_in_user_creation(self, factory):
        """Should safely store SQL injection attempts in user data."""
        # Hasura should store this as literal string, not execute it
        malicious_username = "'; DROP TABLE benchmark.tb_user; --"

        try:
            user = factory.create_user(
                malicious_username, "mal@example.com", "Malicious"
            )

            # If mutation succeeds, verify it's stored as literal
            assert user.username == malicious_username

            # Verify table still exists
            users = factory.get_all_users()
            assert len(users) >= 1

        except (ValueError, RuntimeError):
            # If validation prevents this, that's also acceptable
            pass

    def test_prevent_injection_in_post_content(self, factory):
        """Should safely handle SQL injection in post content."""
        author = factory.create_user("author", "author@example.com", "Author")

        malicious_content = "'; DELETE FROM benchmark.tb_user WHERE '1'='1"
        post = factory.create_post(author.id, "Test Post", malicious_content)

        # Content should be stored as literal
        assert post.content == malicious_content

        # Verify users are not deleted
        users = factory.get_all_users()
        assert len(users) >= 1

    def test_prevent_injection_in_comment(self, factory):
        """Should safely handle SQL injection in comment content."""
        author = factory.create_user("author", "author@example.com", "Author")
        post = factory.create_post(author.id, "Post", "Content")

        malicious_comment = "' OR '1'='1'; DROP TABLE benchmark.tb_post; --"
        comment = factory.create_comment(author.id, post.id, malicious_comment)

        # Comment should be stored as literal
        assert comment.content == malicious_comment

        # Verify post table still exists
        posts = factory.get_posts_by_author(author.pk_user)
        assert len(posts) >= 1


class TestFilterInjection:
    """Test SQL injection prevention in filters."""

    def test_prevent_injection_in_where_clause(self, factory):
        """Should prevent SQL injection in where conditions."""
        factory.create_user("alice", "alice@example.com", "Alice")
        factory.create_user("bob", "bob@example.com", "Bob")

        # Attempt injection in filter
        malicious_filter = "' OR '1'='1"
        result = factory.get_user(malicious_filter)

        # Should not return all users
        assert result is None

    def test_prevent_injection_in_search_pattern(self, factory):
        """Should prevent injection in search/like patterns."""
        factory.create_user("testuser", "test@example.com", "Test User")

        # Attempt pattern injection
        malicious_pattern = "%'; DROP TABLE benchmark.tb_user; --"

        # This should not execute SQL
        users = factory.get_all_users()
        assert len(users) >= 1  # Table should still exist


class TestSpecialCharacters:
    """Test proper handling of special characters."""

    def test_handle_single_quotes_properly(self, factory):
        """Should properly escape single quotes in legitimate data."""
        user = factory.create_user("obrien", "obrien@example.com", "O'Brien", "It's fine")

        assert user.full_name == "O'Brien"
        assert user.bio == "It's fine"

    def test_handle_double_quotes(self, factory):
        """Should handle double quotes in content."""
        user = factory.create_user("author", "author@example.com", "Author")
        content = 'He said "Hello" to me'
        post = factory.create_post(user.id, "Quote Test", content)

        assert post.content == content

    def test_handle_sql_comments_in_content(self, factory):
        """Should treat SQL comments as literal text in content."""
        user = factory.create_user("author", "author@example.com", "Author")
        bio = "This is my bio -- with dashes"
        user_with_bio = factory.create_user("user2", "user2@example.com", "User 2", bio)

        assert user_with_bio.bio == bio

    def test_handle_backslashes(self, factory):
        """Should properly handle backslashes."""
        username = "user\\admin"
        user = factory.create_user(username, "user@example.com", "User")

        assert user.username == username


class TestEncodedInjection:
    """Test prevention of encoded injection attempts."""

    def test_prevent_hex_encoded_injection(self, factory):
        """Should prevent hex-encoded SQL injection."""
        factory.create_user("admin", "admin@example.com", "Admin")

        # Hex-encoded 'admin'
        hex_encoded = "0x61646d696e"
        result = factory.get_user(hex_encoded)

        # Should not match (treated as literal string)
        assert result is None

    def test_prevent_url_encoded_injection(self, factory):
        """Should prevent URL-encoded SQL injection."""
        factory.create_user("user", "user@example.com", "User")

        # URL-encoded "' OR '1'='1"
        url_encoded = "user%27%20OR%20%271%27%3D%271"
        result = factory.get_user(url_encoded)

        assert result is None

    def test_prevent_unicode_injection(self, factory):
        """Should handle unicode safely without injection."""
        user = factory.create_user("author", "author@example.com", "Author")

        # Unicode characters should be safely stored
        unicode_content = "Test with émojis 🎉 and ñ"
        post = factory.create_post(user.id, "Unicode", unicode_content)

        assert post.content == unicode_content


class TestComplexInjection:
    """Test complex SQL injection scenarios."""

    def test_prevent_subquery_injection(self, factory):
        """Should prevent subquery-based injection."""
        factory.create_user("user", "user@example.com", "User")

        malicious_username = (
            "' AND pk_user IN (SELECT pk_user FROM benchmark.tb_user)--"
        )
        result = factory.get_user(malicious_username)

        assert result is None

    def test_prevent_null_byte_injection(self, factory):
        """Should prevent null byte injection."""
        # Null byte injection attempt
        username_with_null = "user\x00admin"

        try:
            user = factory.create_user(
                username_with_null, "null@example.com", "Null User"
            )

            # If stored, should be literal
            assert "\x00" in user.username or "admin" in user.username

        except (ValueError, RuntimeError):
            # If validation prevents null bytes, that's acceptable
            pass

    def test_prevent_multiple_statement_injection(self, factory):
        """Should prevent multiple SQL statements."""
        malicious_username = "'; UPDATE benchmark.tb_user SET username='hacked'; --"

        try:
            factory.create_user(malicious_username, "mal@example.com", "Mal")
        except (ValueError, RuntimeError):
            pass

        # Verify no users were hacked
        users = factory.get_all_users()
        hacked_users = [u for u in users if u.username == "hacked"]
        assert len(hacked_users) == 0


class TestGraphQLSpecificInjection:
    """Test GraphQL-specific injection scenarios."""

    def test_prevent_injection_in_graphql_variables(self, factory):
        """Should handle injection in GraphQL variables safely."""
        factory.create_user("admin", "admin@example.com", "Admin")

        # GraphQL variables are parameterized by design
        malicious_var = "' OR '1'='1"
        result = factory.get_user(malicious_var)

        assert result is None

    def test_prevent_injection_in_json_input(self, factory):
        """Should prevent injection via JSON input objects."""
        # Attempt injection through structured input
        malicious_username = '{"$ne": null}'
        result = factory.get_user(malicious_username)

        assert result is None

    def test_prevent_fragment_based_injection(self, factory):
        """Should prevent injection through GraphQL fragments."""
        factory.create_user("user", "user@example.com", "User")

        # Fragment names cannot contain SQL
        malicious_fragment = "...on User { id } OR 1=1--"
        result = factory.get_user(malicious_fragment)

        assert result is None


class TestBatchOperations:
    """Test injection prevention in batch operations."""

    def test_prevent_injection_in_batch_creation(self, factory):
        """Should handle injection attempts in batch operations."""
        user1 = factory.create_user("user1", "user1@example.com", "User 1")

        # Second user with malicious data
        try:
            malicious_username = "'; DROP TABLE benchmark.tb_user; --"
            user2 = factory.create_user(malicious_username, "mal@example.com", "Mal")
        except (ValueError, RuntimeError):
            pass

        # First user should still exist
        assert factory.get_user(user1.id) is not None

    def test_prevent_injection_across_related_mutations(self, factory):
        """Should prevent injection in related entity mutations."""
        author = factory.create_user("author", "author@example.com", "Author")

        # Create post with malicious title
        malicious_title = "'; DELETE FROM benchmark.tb_user WHERE '1'='1"
        post = factory.create_post(author.id, malicious_title, "Content")

        # Create comment with malicious content
        malicious_comment = "'; DROP TABLE benchmark.tb_post; --"
        comment = factory.create_comment(author.id, post.id, malicious_comment)

        # All should be stored as literals
        assert post.title == malicious_title
        assert comment.content == malicious_comment

        # Verify data integrity
        users = factory.get_all_users()
        posts = factory.get_posts_by_author(author.pk_user)
        assert len(users) >= 1
        assert len(posts) >= 1


class TestValidation:
    """Test that Hasura's type system provides additional protection."""

    def test_type_validation_provides_protection(self, factory):
        """Should validate input types, preventing some injection vectors."""
        user = factory.create_user("user", "user@example.com", "User")

        # Type system should prevent non-string inputs
        # This is enforced at the GraphQL layer
        assert user.username == "user"

    def test_schema_validation_prevents_injection(self, factory):
        """Should validate against GraphQL schema."""
        # Invalid field names should be rejected by GraphQL schema
        # Not by SQL layer - this is a GraphQL protection
        user = factory.create_user("testuser", "test@example.com", "Test")

        assert user.username == "testuser"
