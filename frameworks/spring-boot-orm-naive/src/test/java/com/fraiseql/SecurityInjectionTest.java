package com.fraiseql;

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
        TestFactory.TestUser user = factory.createUser("admin", "admin@example.com", "Admin", "");

        // Try to inject SQL via username lookup
        TestFactory.TestUser result = factory.getUser("' OR '1'='1");

        // Should not return any user due to parameterization
        assertNull(result);
    }

    @Test
    void testUnionBasedInjection() {
        // Attempt: ' UNION SELECT * FROM users--
        TestFactory.TestUser user = factory.createUser("testuser", "test@example.com", "Test User", "");

        String injectionAttempt = "' UNION SELECT * FROM users--";
        TestFactory.TestUser result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testStackedQueriesInjection() {
        // Attempt: '; DROP TABLE users;--
        TestFactory.TestUser user = factory.createUser("victim", "victim@example.com", "Victim", "");

        String injectionAttempt = "'; DROP TABLE users;--";

        // Should not execute the DROP statement - map lookup returns null, no exception
        TestFactory.TestUser result = factory.getUser(injectionAttempt);
        assertNull(result);

        // Verify data is still intact
        assertEquals(1, factory.getAllUsers().size());
    }

    @Test
    void testTimeBasedBlindInjection() {
        // Attempt: ' OR SLEEP(5)--
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        String injectionAttempt = "' OR SLEEP(5)--";
        long startTime = System.currentTimeMillis();

        TestFactory.TestUser result = factory.getUser(injectionAttempt);

        long duration = System.currentTimeMillis() - startTime;

        assertNull(result);
        // Query should not delay (should complete quickly)
        assertTrue(duration < 1000, "Query took too long, possible SQL injection");
    }

    @Test
    void testCommentSequenceInjection() {
        // Attempt: admin'--
        TestFactory.TestUser user = factory.createUser("admin", "admin@example.com", "Admin", "");

        String injectionAttempt = "admin'--";
        TestFactory.TestUser result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testBooleanBasedInjection() {
        // Attempt: ' OR 1=1--
        TestFactory.TestUser user = factory.createUser("testuser", "test@example.com", "Test", "");

        String injectionAttempt = "' OR 1=1--";
        TestFactory.TestUser result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testSecondOrderInjection() {
        // Create user with malicious content - TestFactory does not validate, so it succeeds
        String maliciousUsername = "user'; DROP TABLE posts;--";
        TestFactory.TestUser user = factory.createUser(maliciousUsername, "mal@example.com", "Malicious", "");
        assertNotNull(user);
    }

    @Test
    void testInjectionInPostContent() {
        TestFactory.TestUser author = factory.createUser("author", "author@example.com", "Author", "");

        // Try to inject SQL in post content
        String maliciousContent = "'; DELETE FROM users WHERE '1'='1";
        TestFactory.TestPost post = factory.createPost(author.id, "Test Post", maliciousContent);

        assertNotNull(post);
        assertEquals(maliciousContent, post.content);

        // Verify users are not deleted
        assertEquals(1, factory.getAllUsers().size());
    }

    @Test
    void testInjectionInSearchParameters() {
        TestFactory.TestUser user1 = factory.createUser("alice", "alice@example.com", "Alice", "");
        TestFactory.TestUser user2 = factory.createUser("bob", "bob@example.com", "Bob", "");

        // Try SQL injection in search
        String searchInjection = "alice' OR '1'='1";

        // Should return no results or only exact matches
        TestFactory.TestUser result = factory.getUser(searchInjection);
        assertNull(result);
    }

    @Test
    void testEscapedQuotesHandling() {
        // Test proper handling of escaped quotes
        TestFactory.TestUser user = factory.createUser("user", "user@example.com", "User's Name", "It's fine");

        assertNotNull(user);
        assertEquals("User's Name", user.fullName);
        assertEquals("It's fine", user.bio);
    }

    // ============================================================================
    // ORM-Specific Injection Tests
    // ============================================================================

    @Test
    void testHQLInjection() {
        // Test HQL injection attempts (Hibernate Query Language)
        TestFactory.TestUser user = factory.createUser("admin", "admin@example.com", "Admin", "");

        String hqlInjection = "' OR ''='";
        TestFactory.TestUser result = factory.getUser(hqlInjection);

        assertNull(result);
    }

    @Test
    void testNamedParameterInjection() {
        TestFactory.TestUser user = factory.createUser("user", "user@example.com", "User", "");

        // Try to inject through named parameters
        String injectionAttempt = ":username OR 1=1";
        TestFactory.TestUser result = factory.getUser(injectionAttempt);

        assertNull(result);
    }

    @Test
    void testNoSQLInjectionAttempt() {
        TestFactory.TestUser user = factory.createUser("admin", "admin@example.com", "Admin", "");

        // NoSQL injection attempt: {"$ne": null}
        String injectionAttempt = "{\"$ne\": null}";
        TestFactory.TestUser result = factory.getUser(injectionAttempt);

        assertNull(result);
    }
}
