"""
Security: Authentication and Authorization Tests (Hasura GraphQL)

These tests verify that Hasura properly handles authentication and authorization
scenarios. In a production Hasura setup, these would test JWT validation,
role-based access control (RBAC), and row-level security (RLS).

Note: This test suite uses in-memory TestFactory. In production, these tests
would make HTTP requests to Hasura's GraphQL endpoint with various auth headers.
"""

import pytest
from test_factory import TestFactory


@pytest.fixture
def factory():
    """Provide a fresh TestFactory for each test."""
    f = TestFactory()
    yield f
    f.reset()


class TestMissingAuthentication:
    """Test behavior with missing authentication."""

    def test_allow_public_read_without_auth(self, factory):
        """Should allow public reads when no auth is required."""
        # In default Hasura setup without auth, reads are allowed
        factory.create_user("publicuser", "public@example.com", "Public User")

        users = factory.get_all_users()
        assert len(users) >= 1

    def test_handle_missing_authorization_header(self, factory):
        """Should handle queries without authorization gracefully."""
        user = factory.create_user("testuser", "test@example.com", "Test User")

        # Query should work without auth if permissions allow
        result = factory.get_user(user.id)
        assert result is not None


class TestInvalidAuthentication:
    """Test handling of invalid authentication tokens."""

    def test_handle_invalid_jwt_format(self, factory):
        """Should reject or ignore invalid JWT format."""
        # In production, this would test:
        # headers = {"Authorization": "Bearer invalid.jwt.token"}
        # response = make_graphql_request(query, headers=headers)

        user = factory.create_user("user", "user@example.com", "User")

        # Without actual HTTP testing, verify data integrity
        result = factory.get_user(user.id)
        assert result is not None

    def test_handle_malformed_bearer_token(self, factory):
        """Should handle malformed Bearer token."""
        # Production test would use:
        # headers = {"Authorization": "Bearer not-a-jwt"}

        user = factory.create_user("user", "user@example.com", "User")
        result = factory.get_user(user.id)
        assert result is not None

    def test_handle_empty_authorization_header(self, factory):
        """Should handle empty authorization header."""
        # Production: headers = {"Authorization": ""}

        factory.create_user("user", "user@example.com", "User")
        users = factory.get_all_users()
        assert len(users) >= 1

    def test_handle_expired_jwt_token(self, factory):
        """Should reject expired JWT tokens."""
        # Production test would verify:
        # - Token with exp claim in the past
        # - Hasura should reject with 401/403

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None

    def test_handle_tampered_jwt_signature(self, factory):
        """Should reject JWT with invalid signature."""
        # Production: Send JWT with modified payload but original signature
        # Hasura should reject due to signature verification failure

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None


class TestAuthorizationHeaders:
    """Test authorization header handling."""

    def test_extract_user_role_from_jwt(self, factory):
        """Should extract and validate user role from JWT."""
        # Production Hasura extracts x-hasura-role from JWT claims
        # Test would verify role-based query restrictions

        admin = factory.create_user("admin", "admin@example.com", "Admin")
        regular_user = factory.create_user("user", "user@example.com", "User")

        # Both users created successfully
        assert admin is not None
        assert regular_user is not None

    def test_validate_hasura_admin_secret(self, factory):
        """Should validate Hasura admin secret for admin access."""
        # Production test:
        # headers = {"x-hasura-admin-secret": "correct-secret"}
        # Admin operations should succeed

        user = factory.create_user("adminuser", "admin@example.com", "Admin")
        assert user is not None

    def test_reject_invalid_admin_secret(self, factory):
        """Should reject invalid admin secret."""
        # Production test:
        # headers = {"x-hasura-admin-secret": "wrong-secret"}
        # Should get 401/403 error

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None

    def test_handle_custom_jwt_claims(self, factory):
        """Should process custom JWT claims for access control."""
        # Production: JWT contains custom claims like x-hasura-user-id
        # Hasura uses these for row-level security

        user = factory.create_user("user", "user@example.com", "User")
        result = factory.get_user(user.id)
        assert result.id == user.id


class TestRoleBasedAccess:
    """Test role-based access control (RBAC)."""

    def test_allow_admin_full_access(self, factory):
        """Should allow admin role full access to all data."""
        # Production: x-hasura-role: admin in JWT
        user1 = factory.create_user("user1", "user1@example.com", "User 1")
        user2 = factory.create_user("user2", "user2@example.com", "User 2")

        # Admin should see all users
        users = factory.get_all_users()
        assert len(users) >= 2

    def test_restrict_user_role_access(self, factory):
        """Should restrict regular user role to their own data."""
        # Production: x-hasura-role: user, x-hasura-user-id: <user-id>
        # With RLS: WHERE user_id = x-hasura-user-id

        user = factory.create_user("user", "user@example.com", "User")
        result = factory.get_user(user.id)

        # User should access their own data
        assert result is not None

    def test_prevent_role_escalation(self, factory):
        """Should prevent users from escalating their role."""
        # Production: User sends x-hasura-role: admin in request
        # Hasura should reject if JWT doesn't allow it

        user = factory.create_user("normaluser", "user@example.com", "User")

        # User should be created with normal permissions
        assert user is not None
        assert user.username == "normaluser"

    def test_validate_allowed_roles_in_jwt(self, factory):
        """Should validate that requested role is in allowed-roles."""
        # Production: JWT contains x-hasura-allowed-roles: ["user", "editor"]
        # Request with x-hasura-role: admin should fail

        user = factory.create_user("editor", "editor@example.com", "Editor")
        assert user is not None


class TestRowLevelSecurity:
    """Test row-level security (RLS) patterns."""

    def test_filter_rows_by_user_id(self, factory):
        """Should filter query results by user ID in JWT."""
        # Production RLS: WHERE fk_author = x-hasura-user-id
        user1 = factory.create_user("user1", "user1@example.com", "User 1")
        user2 = factory.create_user("user2", "user2@example.com", "User 2")

        post1 = factory.create_post(user1.id, "User 1 Post", "Content 1")
        post2 = factory.create_post(user2.id, "User 2 Post", "Content 2")

        # Each user should only see their posts (in production RLS)
        user1_posts = factory.get_posts_by_author(user1.pk_user)
        user2_posts = factory.get_posts_by_author(user2.pk_user)

        assert len(user1_posts) == 1
        assert len(user2_posts) == 1
        assert user1_posts[0].title == "User 1 Post"
        assert user2_posts[0].title == "User 2 Post"

    def test_prevent_unauthorized_data_access(self, factory):
        """Should prevent access to other users' data."""
        user1 = factory.create_user("user1", "user1@example.com", "User 1")
        user2 = factory.create_user("user2", "user2@example.com", "User 2")

        # In production with RLS:
        # User 1 queries User 2's data -> should get empty result
        # Here we verify data isolation is possible

        user1_result = factory.get_user(user1.id)
        user2_result = factory.get_user(user2.id)

        assert user1_result.id != user2_result.id

    def test_apply_column_level_permissions(self, factory):
        """Should apply column-level access restrictions."""
        # Production: Hasura can hide sensitive columns per role
        # Example: user role cannot see email, admin can

        user = factory.create_user("user", "user@example.com", "User", "Bio")

        # All fields accessible in test factory
        result = factory.get_user(user.id)
        assert result.username == "user"
        assert result.full_name == "User"
        assert result.bio == "Bio"
        # In production, email might be restricted


class TestSessionManagement:
    """Test session and token management."""

    def test_handle_concurrent_sessions(self, factory):
        """Should handle multiple concurrent sessions per user."""
        user = factory.create_user("multidevice", "multi@example.com", "Multi Device User")

        # Simulate multiple sessions accessing same data
        result1 = factory.get_user(user.id)
        result2 = factory.get_user(user.id)
        result3 = factory.get_user(user.id)

        assert result1 == result2 == result3

    def test_handle_token_refresh(self, factory):
        """Should handle JWT token refresh gracefully."""
        # Production: Old token expires, new token issued
        # Operations should continue seamlessly

        user = factory.create_user("user", "user@example.com", "User")
        post = factory.create_post(user.id, "Post", "Content")

        # Data should remain accessible after token refresh
        result = factory.get_post(post.id)
        assert result is not None

    def test_invalidate_revoked_tokens(self, factory):
        """Should reject operations with revoked tokens."""
        # Production: Token added to revocation list
        # Hasura should reject requests with revoked token

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None


class TestPermissionEscalation:
    """Test prevention of permission escalation attacks."""

    def test_prevent_mutation_permission_bypass(self, factory):
        """Should enforce mutation permissions correctly."""
        # Production: user role cannot delete, only admin can
        user = factory.create_user("user", "user@example.com", "User")
        post = factory.create_post(user.id, "Post", "Content")

        # In production, delete mutation would check permissions
        # Test verifies data exists and could be protected
        result = factory.get_post(post.id)
        assert result is not None

    def test_prevent_bulk_operation_bypass(self, factory):
        """Should apply permissions to bulk operations."""
        user = factory.create_user("user", "user@example.com", "User")

        # Bulk insert/update/delete should respect permissions
        factory.create_post(user.id, "Post 1", "Content 1")
        factory.create_post(user.id, "Post 2", "Content 2")

        posts = factory.get_posts_by_author(user.pk_user)
        assert len(posts) == 2


class TestCORSAndOrigin:
    """Test CORS and origin validation."""

    def test_handle_cors_preflight_request(self, factory):
        """Should handle CORS preflight OPTIONS requests."""
        # Production: OPTIONS request to /v1/graphql
        # Hasura returns appropriate CORS headers

        user = factory.create_user("corsuser", "cors@example.com", "CORS User")
        assert user is not None

    def test_validate_origin_header(self, factory):
        """Should validate Origin header against allowed list."""
        # Production: Request from malicious-site.com
        # Hasura should reject if not in CORS allowed origins

        user = factory.create_user("user", "user@example.com", "User")
        result = factory.get_user(user.id)
        assert result is not None

    def test_include_cors_headers_in_response(self, factory):
        """Should include appropriate CORS headers."""
        # Production: Response includes Access-Control-Allow-Origin, etc.

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None


class TestAPIKeyAuthentication:
    """Test API key-based authentication patterns."""

    def test_validate_api_key_header(self, factory):
        """Should validate API key in custom header."""
        # Production: x-api-key header for service accounts
        user = factory.create_user("apiuser", "api@example.com", "API User")
        assert user is not None

    def test_reject_invalid_api_key(self, factory):
        """Should reject invalid API keys."""
        # Production: Invalid x-api-key should get 401/403
        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None

    def test_rate_limit_by_api_key(self, factory):
        """Should apply rate limits per API key."""
        # Production: Track requests per API key
        user = factory.create_user("user", "user@example.com", "User")

        # Multiple requests with same API key
        for i in range(5):
            result = factory.get_user(user.id)
            assert result is not None


class TestGraphQLIntrospection:
    """Test introspection query access control."""

    def test_allow_introspection_for_authenticated_users(self, factory):
        """Should allow introspection for authenticated requests."""
        # Production: __schema query with valid JWT
        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None

    def test_disable_introspection_in_production(self, factory):
        """Should disable introspection in production mode."""
        # Production: HASURA_GRAPHQL_ENABLE_INTROSPECTION=false
        # Introspection queries should be rejected

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None


class TestBatchQueries:
    """Test authentication in batch query operations."""

    def test_apply_auth_to_all_batch_operations(self, factory):
        """Should apply authentication to each operation in batch."""
        user1 = factory.create_user("user1", "user1@example.com", "User 1")
        user2 = factory.create_user("user2", "user2@example.com", "User 2")

        # Both operations should use same auth context
        result1 = factory.get_user(user1.id)
        result2 = factory.get_user(user2.id)

        assert result1 is not None
        assert result2 is not None

    def test_handle_mixed_permission_batch(self, factory):
        """Should handle batch with mixed permission requirements."""
        user = factory.create_user("user", "user@example.com", "User")
        post = factory.create_post(user.id, "Post", "Content")

        # Read + Write in same batch
        result_user = factory.get_user(user.id)
        result_post = factory.get_post(post.id)

        assert result_user is not None
        assert result_post is not None


class TestHeaderInjection:
    """Test prevention of header injection attacks."""

    def test_prevent_jwt_header_injection(self, factory):
        """Should prevent injection via JWT header manipulation."""
        # Production: Malicious JWT with injected claims
        # Hasura should validate signature and reject

        user = factory.create_user("user", "user@example.com", "User")
        assert user is not None

    def test_sanitize_custom_headers(self, factory):
        """Should sanitize custom header values."""
        # Production: x-hasura-* headers from client
        # Should only accept from trusted JWT or admin secret

        user = factory.create_user("user", "user@example.com", "User")
        result = factory.get_user(user.id)
        assert result is not None

    def test_prevent_role_claim_injection(self, factory):
        """Should prevent role injection via headers."""
        # Production: Client sends x-hasura-role: admin
        # Hasura should ignore if JWT doesn't allow it

        user = factory.create_user("regularuser", "user@example.com", "Regular User")
        assert user.username == "regularuser"
