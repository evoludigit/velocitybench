package com.velocitybench;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * SQL Injection Prevention Test Suite for Spring GraphQL
 * Tests that the application properly handles malicious SQL injection attempts.
 */
class SecurityInjectionTest {
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
    // SQL Injection Prevention Tests
    // ============================================================================

    @Test
    void testBasicOrInjection() {
        // Attempt: ' OR '1'='1
        var user = factory.createUser("admin", "admin@example.com", "Admin");

        // Try to inject SQL via username lookup
        var result = factory.getUser("' OR '1'='1");

        // Should not return any user due to parameterization
        assertNull(result);
    }

    @Test
    void testUnionBasedInjection() {
        // Attempt: ' UNION SELECT * FROM users--
        var user = factory.createUser("testuser", "test@example.com", "Test User");

        String injectionAttempt = "' UNION SELECT * FROM users--";
        var result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testStackedQueriesInjection() {
        // Attempt: '; DROP TABLE users;--
        var user = factory.createUser("victim", "victim@example.com", "Victim");

        String injectionAttempt = "'; DROP TABLE users;--";

        // Should not execute the DROP statement
        var result = factory.getUser(injectionAttempt);
        assertNull(result);

        // Verify data is still intact
        assertEquals(1, factory.getAllUsers().size());
    }

    @Test
    void testTimeBasedBlindInjection() {
        // Attempt: ' OR SLEEP(5)--
        var user = factory.createUser("user1", "user1@example.com", "User 1");

        String injectionAttempt = "' OR SLEEP(5)--";
        long startTime = System.currentTimeMillis();

        var result = factory.getUser(injectionAttempt);

        long duration = System.currentTimeMillis() - startTime;

        assertNull(result);
        // Query should not delay (should complete quickly)
        assertTrue(duration < 1000, "Query took too long, possible SQL injection");
    }

    @Test
    void testCommentSequenceInjection() {
        // Attempt: admin'--
        var user = factory.createUser("admin", "admin@example.com", "Admin");

        String injectionAttempt = "admin'--";
        var result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testBooleanBasedInjection() {
        // Attempt: ' OR 1=1--
        var user = factory.createUser("testuser", "test@example.com", "Test");

        String injectionAttempt = "' OR 1=1--";
        var result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testSecondOrderInjection() {
        // Create user with malicious content
        String maliciousUsername = "user'; DROP TABLE posts;--";

        // Should either sanitize or reject
        assertThrows(RuntimeException.class, () -> {
            factory.createUser(maliciousUsername, "mal@example.com", "Malicious");
        });
    }

    @Test
    void testInjectionInPostContent() {
        var author = factory.createUser("author", "author@example.com", "Author");

        // Try to inject SQL in post content
        String maliciousContent = "'; DELETE FROM users WHERE '1'='1";
        var post = factory.createPost(author.id, "Test Post", maliciousContent);

        assertNotNull(post);
        assertEquals(maliciousContent, post.content);

        // Verify users are not deleted
        assertEquals(1, factory.getAllUsers().size());
    }

    @Test
    void testInjectionInSearchParameters() {
        var user1 = factory.createUser("alice", "alice@example.com", "Alice");
        var user2 = factory.createUser("bob", "bob@example.com", "Bob");

        // Try SQL injection in search
        String searchInjection = "alice' OR '1'='1";

        // Should return no results or only exact matches
        var result = factory.getUser(searchInjection);
        assertNull(result);
    }

    @Test
    void testEscapedQuotesHandling() {
        // Test proper handling of escaped quotes
        var user = factory.createUser("user", "user@example.com", "User's Name", "It's fine");

        assertNotNull(user);
        assertEquals("User's Name", user.fullName);
        assertEquals("It's fine", user.bio);
    }

    // ============================================================================
    // GraphQL-Specific Injection Tests
    // ============================================================================

    @Test
    void testGraphQLInjectionInVariables() {
        var user = factory.createUser("admin", "admin@example.com", "Admin");

        // Try to inject through GraphQL variables
        String injectionAttempt = "{ \"id\": \"' OR '1'='1\" }";
        var result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testGraphQLFragmentInjection() {
        var user = factory.createUser("user", "user@example.com", "User");

        // Attempt fragment-based injection
        String fragmentInjection = "...on User { id } OR 1=1--";
        var result = factory.getUser(fragmentInjection);

        assertNull(result);
    }

    @Test
    void testNoSQLInjectionAttempt() {
        var user = factory.createUser("admin", "admin@example.com", "Admin");

        // NoSQL injection attempt: {"$ne": null}
        String injectionAttempt = "{\"$ne\": null}";
        var result = factory.getUser(injectionAttempt);

        assertNull(result);
    }
}
