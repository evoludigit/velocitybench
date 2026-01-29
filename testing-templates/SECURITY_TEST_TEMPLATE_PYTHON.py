"""
TEMPLATE: Security Test Suite for Python Frameworks
====================================================

This is a master template for generating security tests across all Python frameworks.
Use this as the pattern for SQL injection, auth validation, and rate limiting tests.

Copy to: frameworks/{framework}/tests/test_security_injection.py
         frameworks/{framework}/tests/test_security_auth.py
         frameworks/{framework}/tests/test_security_rate_limit.py

Instructions:
1. Replace {TestFramework} with actual framework (FastAPI, Flask, Strawberry, etc.)
2. Replace {factory_methods} with actual factory calls for framework
3. Replace {expected_exceptions} with framework-specific exceptions
4. Replace {api_endpoint} with actual endpoint pattern

The core test assertions should remain identical across all frameworks.
"""

import pytest


# ============================================================================
# SQL INJECTION PREVENTION TESTS
# ============================================================================

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
        result = factory.get_user_by_username(injection_payload)

        # Assert - Should find the user with literal injection string as username
        assert result is not None
        assert result['username'] == injection_payload
        assert result['id'] == user['id']

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
        result = factory.get_user_by_username(injection_payload)

        # Assert
        assert result is not None
        assert result['username'] == injection_payload

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
        result = factory.get_user_by_username(injection_payload)

        # Verify table still exists and data is intact
        assert result is not None
        assert result['username'] == injection_payload

        # Verify other users still exist
        all_users = factory.get_all_users()
        assert len(all_users) >= 1

    def test_time_based_blind_injection(self, factory, db):
        """Should not allow time-based blind SQL injection.

        Input: test' AND SLEEP(5) --
        Attack Type: Time-based blind injection
        Expected: Query returns quickly (no sleep execution)
        """
        # Arrange
        import time
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
        for payload in payloads:
            user = factory.create_user(payload, f"test{payloads.index(payload)}@example.com")
            result = factory.get_user_by_username(payload)
            assert result is not None
            assert result['username'] == payload


# ============================================================================
# AUTHENTICATION & AUTHORIZATION TESTS
# ============================================================================

@pytest.mark.security
@pytest.mark.security_auth
class TestAuthenticationValidation:
    """Verify authentication cannot be bypassed."""

    def test_missing_auth_token_fails(self, factory):
        """Should reject requests without authentication token.

        Expected: 401 Unauthorized or AuthenticationError
        """
        # Act & Assert
        with pytest.raises((AuthenticationError, ValueError, Exception)) as exc_info:
            factory.get_protected_user_data(auth_token=None)

        # Verify error is auth-related
        error_str = str(exc_info.value).lower()
        assert any(word in error_str for word in ['auth', 'unauthorized', 'token', '401'])

    def test_invalid_token_format_fails(self, factory):
        """Should reject malformed JWT tokens.

        Expected: 401 Unauthorized
        """
        # Arrange
        invalid_tokens = [
            "",
            "invalid",
            "not.a.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Incomplete JWT
            "definitely-not-a-jwt-at-all",
        ]

        # Act & Assert
        for invalid_token in invalid_tokens:
            with pytest.raises((AuthenticationError, ValueError, Exception)):
                factory.get_protected_user_data(auth_token=invalid_token)

    def test_expired_token_fails(self, factory):
        """Should reject expired authentication tokens.

        Expected: 401 Unauthorized
        """
        # Arrange - Create an expired token
        import jwt
        import time

        expired_token = jwt.encode(
            {"exp": int(time.time()) - 3600},  # Expired 1 hour ago
            "secret",
            algorithm="HS256"
        )

        # Act & Assert
        with pytest.raises((AuthenticationError, jwt.ExpiredSignatureError, Exception)):
            factory.get_protected_user_data(auth_token=expired_token)

    def test_token_signature_tampering_fails(self, factory):
        """Should reject tokens with tampered signatures.

        Expected: 401 Unauthorized
        """
        # Arrange - Get valid token and tamper with it
        user = factory.create_user("alice", "alice@example.com")
        valid_token = factory.get_auth_token(user['id'])

        # Tamper with last 10 characters of token
        tampered_token = valid_token[:-10] + "0000000000"

        # Act & Assert
        with pytest.raises((AuthenticationError, Exception)):
            factory.get_protected_user_data(auth_token=tampered_token)

    def test_unauthorized_resource_access_fails(self, factory):
        """Should prevent accessing other users' private data.

        Expected: 403 Forbidden
        """
        # Arrange
        alice = factory.create_user("alice", "alice@example.com")
        bob = factory.create_user("bob", "bob@example.com")

        alice_token = factory.get_auth_token(alice['id'])

        # Act & Assert - Alice should not access Bob's private data
        with pytest.raises((AuthorizationError, PermissionError, Exception)):
            factory.get_user_private_data(bob['id'], auth_token=alice_token)


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

@pytest.mark.security
@pytest.mark.security_rate_limit
class TestRateLimiting:
    """Verify rate limiting prevents abuse."""

    def test_rate_limit_per_user(self, factory):
        """Should enforce per-user rate limits.

        Expected: After N requests, further requests fail with 429 Too Many Requests
        """
        # Arrange
        user = factory.create_user("alice", "alice@example.com")
        token = factory.get_auth_token(user['id'])

        # Define rate limit (example: 100 requests)
        rate_limit = 100

        # Act - Make exactly N requests (should succeed)
        for i in range(rate_limit):
            result = factory.query_users(auth_token=token)
            assert result is not None

        # Assert - N+1 request should fail
        with pytest.raises((RateLimitExceededError, Exception)) as exc_info:
            factory.query_users(auth_token=token)

        error_str = str(exc_info.value).lower()
        assert any(word in error_str for word in ['rate', 'limit', 'throttle', '429'])

    def test_rate_limit_reset_after_window(self, factory):
        """Should reset rate limit counter after time window.

        Expected: After window expires, new requests should succeed
        """
        # Arrange
        user = factory.create_user("alice", "alice@example.com")
        token = factory.get_auth_token(user['id'])

        # Act - Exceed rate limit
        for i in range(101):
            try:
                factory.query_users(auth_token=token)
            except RateLimitExceededError:
                break

        # Wait for rate limit window to reset (or mock time progression)
        import time
        time.sleep(2)  # Wait for reset (adjust based on framework's window)

        # Assert - Should be able to make new requests
        result = factory.query_users(auth_token=token)
        assert result is not None

    def test_rate_limit_different_users_independent(self, factory):
        """Should enforce rate limits per user independently.

        Expected: One user hitting limit should not affect other users
        """
        # Arrange
        alice = factory.create_user("alice", "alice@example.com")
        bob = factory.create_user("bob", "bob@example.com")

        alice_token = factory.get_auth_token(alice['id'])
        bob_token = factory.get_auth_token(bob['id'])

        # Act - Alice hits rate limit
        for i in range(101):
            try:
                factory.query_users(auth_token=alice_token)
            except RateLimitExceededError:
                break

        # Assert - Bob should still be able to make requests
        result = factory.query_users(auth_token=bob_token)
        assert result is not None


# ============================================================================
# INPUT VALIDATION & SANITIZATION TESTS
# ============================================================================

@pytest.mark.security
@pytest.mark.security_validation
class TestInputValidation:
    """Verify input validation prevents injection attacks."""

    def test_xss_script_in_input_escaped(self, factory):
        """Should escape or sanitize HTML/script tags.

        Input: <script>alert('xss')</script>
        Expected: Should not execute script
        """
        # Arrange
        xss_payload = "<script>alert('xss')</script>"

        # Act
        user = factory.create_user("alice", "alice@example.com", xss_payload, "bio")
        result = factory.get_user(user['id'])

        # Assert - Script should be escaped or removed
        assert xss_payload not in result['full_name'] or \
               result['full_name'] != xss_payload or \
               "script" not in result['full_name'].lower()

    def test_html_entities_handled(self, factory):
        """Should handle HTML entities safely.

        Input: &lt;script&gt;
        Expected: Should be treated as literal text
        """
        # Arrange
        html_entity = "&lt;script&gt;"

        # Act
        user = factory.create_user("alice", "alice@example.com", html_entity)
        result = factory.get_user(user['id'])

        # Assert
        assert result is not None

    def test_null_byte_injection(self, factory):
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
            assert user is not None
        except (ValueError, Exception):
            # Exception is also valid response to null bytes
            pass


# ============================================================================
# HELPER FUNCTIONS (Framework-Specific)
# ============================================================================

# TODO: Implement framework-specific exceptions and helpers
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass

class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass
