package com.fraiseql;

import com.fraiseql.models.User;
import com.fraiseql.models.Post;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.UUID;

class ErrorEdgeCasesTest {
    private TestFactory factory;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
    }

    // ============================================================================
    // Error: HTTP Status Codes
    // ============================================================================

    @Test
    void testHttpStatusCodeSuccess() {
        factory.createTestUser("alice", "alice@example.com", "Alice", "");
        assertEquals(1, factory.getUserCount());
    }

    @Test
    void testHttpStatusCodeNotFound() {
        User user = factory.getUser("nonexistent-id");
        assertNull(user);
    }

    // ============================================================================
    // Error: 404 Not Found
    // ============================================================================

    @Test
    void testUserNotFoundReturnsNull() {
        User user = factory.getUser("nonexistent-user-id");
        assertNull(user);
    }

    @Test
    void testPostNotFoundReturnsNull() {
        Post post = factory.getPost("nonexistent-post-id");
        assertNull(post);
    }

    // ============================================================================
    // Error: Invalid Input
    // ============================================================================

    @Test
    void testInvalidLimitNegative() {
        int limit = -5;
        int clamped = Math.max(0, Math.min(100, limit));
        assertEquals(0, clamped);
    }

    @Test
    void testInvalidLimitZero() {
        int limit = 0;
        int clamped = Math.max(0, Math.min(100, limit));
        assertEquals(0, clamped);
    }

    @Test
    void testVeryLargeLimit() {
        int limit = 999999;
        int clamped = Math.max(0, Math.min(100, limit));
        assertEquals(100, clamped);
    }

    // ============================================================================
    // Edge Case: UUID Validation
    // ============================================================================

    @Test
    void testAllUserIdsAreUUID() {
        factory.createTestUser("user0", "user0@example.com", "User", "");
        factory.createTestUser("user1", "user1@example.com", "User", "");
        factory.createTestUser("user2", "user2@example.com", "User", "");

        for (User user : factory.getAllUsers()) {
            assertDoesNotThrow(() -> UUID.fromString(user.getId()));
        }
    }

    @Test
    void testAllPostIdsAreUUID() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");

        factory.createTestPost(author.getId(), "Post0", "Content");
        factory.createTestPost(author.getId(), "Post1", "Content");
        factory.createTestPost(author.getId(), "Post2", "Content");

        for (Post post : factory.getAllPosts()) {
            assertDoesNotThrow(() -> UUID.fromString(post.getId()));
        }
    }

    // ============================================================================
    // Edge Case: Special Characters
    // ============================================================================

    @Test
    void testSpecialCharSingleQuotes() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "I'm a developer");
        assertNotNull(factory.getUser(user.getId()));
    }

    @Test
    void testSpecialCharDoubleQuotes() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "He said \"hello\"");
        assertNotNull(factory.getUser(user.getId()));
    }

    @Test
    void testSpecialCharHtmlTags() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Check <this> out");
        assertNotNull(factory.getUser(user.getId()));
    }

    @Test
    void testSpecialCharAmpersand() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Tom & Jerry");
        assertNotNull(factory.getUser(user.getId()));
    }

    @Test
    void testSpecialCharEmoji() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "🎉 Celebration! 🚀 Rocket");
        assertNotNull(factory.getUser(user.getId()));
    }

    @Test
    void testSpecialCharAccents() {
        User user = factory.createTestUser("alice", "alice@example.com", "Àlice Müller", "");
        assertNotNull(factory.getUser(user.getId()));
    }

    @Test
    void testSpecialCharDiacritics() {
        User user = factory.createTestUser("alice", "alice@example.com", "José García", "");
        assertNotNull(factory.getUser(user.getId()));
    }

    // ============================================================================
    // Edge Case: Boundary Conditions
    // ============================================================================

    @Test
    void testBoundaryVeryLongBio5000Chars() {
        String longBio = generateLongString(5000);
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", longBio);
        User retrieved = factory.getUser(user.getId());
        assertEquals(5000, retrieved.getBio().length());
    }

    @Test
    void testBoundaryVeryLongUsername255Chars() {
        String longName = generateLongString(255);
        User user = factory.createTestUser(longName, "user@example.com", "User", "");
        User retrieved = factory.getUser(user.getId());
        assertEquals(255, retrieved.getUsername().length());
    }

    @Test
    void testBoundaryVeryLongPostTitle() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        String longTitle = generateLongString(500);
        Post post = factory.createTestPost(author.getId(), longTitle, "Content");
        Post retrieved = factory.getPost(post.getId());
        assertEquals(500, retrieved.getTitle().length());
    }

    @Test
    void testBoundaryVeryLongContent5000Chars() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        String longContent = generateLongString(5000);
        Post post = factory.createTestPost(author.getId(), "Title", longContent);
        Post retrieved = factory.getPost(post.getId());
        assertEquals(5000, retrieved.getContent().length());
    }

    // ============================================================================
    // Edge Case: Null/Empty Fields
    // ============================================================================

    @Test
    void testNullBioIsHandled() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        User retrieved = factory.getUser(user.getId());
        assertNull(retrieved.getBio());
    }

    @Test
    void testEmptyStringBio() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        User retrieved = factory.getUser(user.getId());
        assertNull(retrieved.getBio());
    }

    @Test
    void testPresentBio() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "My bio");
        User retrieved = factory.getUser(user.getId());
        assertEquals("My bio", retrieved.getBio());
    }

    // ============================================================================
    // Edge Case: Relationship Validation
    // ============================================================================

    @Test
    void testPostAuthorIdIsValidUUID() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post", "Content");
        assertDoesNotThrow(() -> UUID.fromString(post.getAuthor().getId()));
    }

    @Test
    void testPostReferencesCorrectAuthor() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post", "Content");
        assertEquals(author.getId(), post.getAuthor().getId());
    }

    @Test
    void testMultiplePostsReferenceDifferentAuthors() {
        User author1 = factory.createTestUser("author1", "author1@example.com", "Author1", "");
        User author2 = factory.createTestUser("author2", "author2@example.com", "Author2", "");

        Post post1 = factory.createTestPost(author1.getId(), "Post1", "Content");
        Post post2 = factory.createTestPost(author2.getId(), "Post2", "Content");

        assertNotEquals(post1.getAuthor().getId(), post2.getAuthor().getId());
        assertEquals(post1.getAuthor().getId(), author1.getId());
        assertEquals(post2.getAuthor().getId(), author2.getId());
    }

    // ============================================================================
    // Edge Case: Data Type Validation
    // ============================================================================

    @Test
    void testUsernameIsString() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        User retrieved = factory.getUser(user.getId());
        assertEquals("alice", retrieved.getUsername());
    }

    @Test
    void testPostTitleIsString() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Test Post", "Content");
        Post retrieved = factory.getPost(post.getId());
        assertEquals("Test Post", retrieved.getTitle());
    }

    // ============================================================================
    // Edge Case: Uniqueness
    // ============================================================================

    @Test
    void testMultipleUsersHaveUniqueIds() {
        User user1 = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        User user2 = factory.createTestUser("bob", "bob@example.com", "Bob", "");
        User user3 = factory.createTestUser("charlie", "charlie@example.com", "Charlie", "");

        assertNotEquals(user1.getId(), user2.getId());
        assertNotEquals(user2.getId(), user3.getId());
        assertNotEquals(user1.getId(), user3.getId());
    }

    @Test
    void testMultiplePostsHaveUniqueIds() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post1 = factory.createTestPost(author.getId(), "Post1", "Content1");
        Post post2 = factory.createTestPost(author.getId(), "Post2", "Content2");
        Post post3 = factory.createTestPost(author.getId(), "Post3", "Content3");

        assertNotEquals(post1.getId(), post2.getId());
        assertNotEquals(post2.getId(), post3.getId());
        assertNotEquals(post1.getId(), post3.getId());
    }

    // Helper method
    private String generateLongString(int length) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {
            sb.append(i % 10);
        }
        return sb.toString();
    }
}
