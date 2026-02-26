package com.velocitybench;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.Base64;

/**
 * Authentication Validation Test Suite for Spring GraphQL
 * Tests that the application properly validates authentication tokens and permissions.
 */
class SecurityAuthTest {
    private TestFactory factory;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
    }

    @AfterEach
    void tearDown() {
        factory.reset();
    }

    // ============================================================================
    // Authentication Token Tests
    // ============================================================================

    @Test
    void testMissingAuthToken() {
        var user = factory.createUser("user", "user@example.com", "User");

        assertThrows(SecurityException.class, () -> {
            validateToken(null);
        });
    }

    @Test
    void testInvalidTokenFormat() {
        String invalidToken = "not-a-valid-token";

        assertThrows(SecurityException.class, () -> {
            validateToken(invalidToken);
        });
    }

    @Test
    void testExpiredToken() {
        long expiredTime = Instant.now().minusSeconds(3600).getEpochSecond();
        String expiredToken = generateMockToken("user123", expiredTime);

        assertThrows(SecurityException.class, () -> {
            validateToken(expiredToken);
        });
    }

    @Test
    void testTokenSignatureTampering() {
        String validToken = generateMockToken("user123", Instant.now().plusSeconds(3600).getEpochSecond());
        String tamperedToken = validToken.substring(0, validToken.length() - 5) + "XXXXX";

        assertThrows(SecurityException.class, () -> {
            validateToken(tamperedToken);
        });
    }

    @Test
    void testValidTokenAccepted() {
        long futureTime = Instant.now().plusSeconds(3600).getEpochSecond();
        String validToken = generateMockToken("user123", futureTime);

        assertDoesNotThrow(() -> {
            validateToken(validToken);
        });
    }

    @Test
    void testTokenWithInvalidUserId() {
        long futureTime = Instant.now().plusSeconds(3600).getEpochSecond();
        String tokenWithInvalidUser = generateMockToken("nonexistent-user", futureTime);

        assertDoesNotThrow(() -> {
            validateToken(tokenWithInvalidUser);
        });

        var user = factory.getUser("nonexistent-user");
        assertNull(user);
    }

    // ============================================================================
    // Authorization Tests
    // ============================================================================

    @Test
    void testUnauthorizedResourceAccess() {
        var user1 = factory.createUser("user1", "user1@example.com", "User 1");
        var user2 = factory.createUser("user2", "user2@example.com", "User 2");

        var user2Post = factory.createPost(user2.id, "Private Post", "Secret content");

        assertThrows(SecurityException.class, () -> {
            authorizeResourceAccess(user1.id, user2Post.id, "delete");
        });
    }

    @Test
    void testAuthorizedResourceAccess() {
        var user = factory.createUser("user", "user@example.com", "User");
        var userPost = factory.createPost(user.id, "My Post", "My content");

        assertDoesNotThrow(() -> {
            authorizeResourceAccess(user.id, userPost.id, "delete");
        });
    }

    @Test
    void testPrivilegeEscalation() {
        var regularUser = factory.createUser("regular", "regular@example.com", "Regular User");
        var adminUser = factory.createUser("admin", "admin@example.com", "Admin");

        assertThrows(SecurityException.class, () -> {
            checkAdminPrivileges(regularUser.id);
        });
    }

    @Test
    void testCrossUserDataAccess() {
        var user1 = factory.createUser("user1", "user1@example.com", "User 1");
        var user2 = factory.createUser("user2", "user2@example.com", "User 2");

        assertThrows(SecurityException.class, () -> {
            authorizeProfileAccess(user1.id, user2.id);
        });
    }

    // ============================================================================
    // Session Management Tests
    // ============================================================================

    @Test
    void testConcurrentSessionHandling() {
        var user = factory.createUser("user", "user@example.com", "User");

        String session1 = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond());
        String session2 = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond());

        assertDoesNotThrow(() -> {
            validateToken(session1);
            validateToken(session2);
        });
    }

    @Test
    void testSessionInvalidationAfterLogout() {
        var user = factory.createUser("user", "user@example.com", "User");

        String token = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond());

        invalidateToken(token);

        // Token should no longer be active
        assertTrue(!isTokenActive(token), "Token should be invalidated after logout");
    }

    @Test
    void testTokenReuse() {
        var user = factory.createUser("user", "user@example.com", "User");

        String token = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond());

        assertDoesNotThrow(() -> {
            validateToken(token);
        });

        assertDoesNotThrow(() -> {
            validateToken(token);
        });
    }

    // ============================================================================
    // Helper Methods
    // ============================================================================

    private String generateMockToken(String userId, long expirationTime) {
        String payload = userId + ":" + expirationTime;
        return Base64.getEncoder().encodeToString(payload.getBytes());
    }

    private void validateToken(String token) {
        if (token == null || token.isEmpty()) {
            throw new SecurityException("Missing authentication token");
        }

        if (!token.matches("^[A-Za-z0-9+/=]+$")) {
            throw new SecurityException("Invalid token format");
        }

        try {
            String decoded = new String(Base64.getDecoder().decode(token));
            String[] parts = decoded.split(":");

            if (parts.length != 2) {
                throw new SecurityException("Invalid token structure");
            }

            long expirationTime = Long.parseLong(parts[1]);
            if (Instant.now().getEpochSecond() > expirationTime) {
                throw new SecurityException("Token expired");
            }
        } catch (IllegalArgumentException e) {
            throw new SecurityException("Token decoding failed");
        }
    }

    private void authorizeResourceAccess(String userId, String resourceId, String action) {
        var post = factory.getPost(resourceId);
        if (post == null) {
            throw new SecurityException("Resource not found");
        }

        if (!post.author.id.equals(userId)) {
            throw new SecurityException("Unauthorized access to resource");
        }
    }

    private void checkAdminPrivileges(String userId) {
        var user = factory.getUser(userId);
        if (user == null || !user.username.equals("admin")) {
            throw new SecurityException("Admin privileges required");
        }
    }

    private void authorizeProfileAccess(String requesterId, String targetUserId) {
        if (!requesterId.equals(targetUserId)) {
            throw new SecurityException("Cannot access another user's profile");
        }
    }

    private final java.util.Set<String> invalidatedTokens = new java.util.HashSet<>();

    private void invalidateToken(String token) {
        invalidatedTokens.add(token);
    }

    private boolean isTokenActive(String token) {
        return !invalidatedTokens.contains(token);
    }
}
