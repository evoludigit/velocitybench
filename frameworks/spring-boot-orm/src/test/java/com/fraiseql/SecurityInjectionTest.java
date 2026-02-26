package com.fraiseql;

import com.fraiseql.entities.User;
import com.fraiseql.entities.Post;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * SQL Injection Prevention Test Suite
 * Tests that the application properly handles malicious SQL injection attempts.
 */
class SecurityInjectionTest {
    private TestFactory factory;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
    }

    // ============================================================================
    // SQL Injection Prevention Tests
    // ============================================================================

    @Test
    void testBasicOrInjection() {
        // Attempt: ' OR '1'='1
        User user = factory.createTestUser("admin", "admin@example.com", "Admin", "");

        // Try to inject SQL via username lookup
        User result = factory.getUser("' OR '1'='1");

        // Should not return any user due to parameterization
        assertNull(result);
    }

    @Test
    void testUnionBasedInjection() {
        // Attempt: ' UNION SELECT * FROM users--
        User user = factory.createTestUser("testuser", "test@example.com", "Test User", "");

        String injectionAttempt = "' UNION SELECT * FROM users--";
        User result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testStackedQueriesInjection() {
        // Attempt: '; DROP TABLE users;--
        User user = factory.createTestUser("victim", "victim@example.com", "Victim", "");

        String injectionAttempt = "'; DROP TABLE users;--";

        // Should not execute the DROP statement - returns null gracefully
        User result = factory.getUser(injectionAttempt);
        assertNull(result);

        // Verify data is still intact
        assertEquals(1, factory.getUserCount());
    }

    @Test
    void testTimeBasedBlindInjection() {
        // Attempt: ' OR SLEEP(5)--
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        String injectionAttempt = "' OR SLEEP(5)--";
        long startTime = System.currentTimeMillis();

        User result = factory.getUser(injectionAttempt);

        long duration = System.currentTimeMillis() - startTime;

        assertNull(result);
        // Query should not delay (should complete quickly)
        assertTrue(duration < 1000, "Query took too long, possible SQL injection");
    }

    @Test
    void testCommentSequenceInjection() {
        // Attempt: admin'--
        User user = factory.createTestUser("admin", "admin@example.com", "Admin", "");

        String injectionAttempt = "admin'--";
        User result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testBooleanBasedInjection() {
        // Attempt: ' OR 1=1--
        User user = factory.createTestUser("testuser", "test@example.com", "Test", "");

        String injectionAttempt = "' OR 1=1--";
        User result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testSecondOrderInjection() {
        // Create user with malicious content
        String maliciousUsername = "user'; DROP TABLE posts;--";

        // The malicious username is stored as-is (sanitized by parameterization)
        User result = factory.createTestUser(maliciousUsername, "mal@example.com", "Malicious", "");

        // Verify no data corruption occurred - data is intact
        assertFalse(factory.getAllUsers().isEmpty(), "Data should remain intact after injection attempt");
    }

    @Test
    void testInjectionInPostContent() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");

        // Try to inject SQL in post content
        String maliciousContent = "'; DELETE FROM users WHERE '1'='1";
        Post post = factory.createTestPost(author.getId(), "Test Post", maliciousContent);

        assertNotNull(post);
        assertEquals(maliciousContent, post.getContent());

        // Verify users are not deleted
        assertEquals(1, factory.getUserCount());
    }

    @Test
    void testInjectionInSearchParameters() {
        User user1 = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        User user2 = factory.createTestUser("bob", "bob@example.com", "Bob", "");

        // Try SQL injection in search
        String searchInjection = "alice' OR '1'='1";

        // Should return no results or only exact matches
        User result = factory.getUser(searchInjection);
        assertNull(result);
    }

    @Test
    void testEscapedQuotesHandling() {
        // Test proper handling of escaped quotes
        User user = factory.createTestUser("user", "user@example.com", "User's Name", "It's fine");

        assertNotNull(user);
        assertEquals("User's Name", user.getFullName());
        assertEquals("It's fine", user.getBio());
    }

    // ============================================================================
    // ORM-Specific Injection Tests
    // ============================================================================

    @Test
    void testHQLInjection() {
        // Test HQL injection attempts (Hibernate Query Language)
        User user = factory.createTestUser("admin", "admin@example.com", "Admin", "");

        String hqlInjection = "' OR ''='";
        User result = factory.getUser(hqlInjection);

        assertNull(result);
    }

    @Test
    void testNamedParameterInjection() {
        User user = factory.createTestUser("user", "user@example.com", "User", "");

        // Try to inject through named parameters
        String injectionAttempt = ":username OR 1=1";
        User result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testNoSQLInjectionAttempt() {
        User user = factory.createTestUser("admin", "admin@example.com", "Admin", "");

        // NoSQL injection attempt: {"$ne": null}
        String injectionAttempt = "{\"$ne\": null}";
        User result = factory.getUser(injectionAttempt);

        assertNull(result);
    }
}
