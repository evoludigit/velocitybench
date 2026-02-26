package com.fraiseql;

import com.fraiseql.models.User;
import com.fraiseql.models.Post;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MutationsTest {
    private TestFactory factory;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
    }

    // ============================================================================
    // Mutation: updateUser
    // ============================================================================

    @Test
    void testUpdateUserFullName() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        // Simulate mutation
        user.setFullName("Alice Smith");

        // Verify
        assertEquals("Alice Smith", user.getFullName());
        assertEquals(userId, user.getId());
    }

    @Test
    void testUpdateUserBio() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        // Simulate mutation
        user.setBio("Senior Developer");

        // Verify
        assertEquals("Senior Developer", user.getBio());
        assertEquals(userId, user.getId());
    }

    @Test
    void testUpdateUserBothFields() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        // Simulate mutation
        user.setFullName("Alice Smith");
        user.setBio("Senior Developer");

        // Verify
        assertEquals("Alice Smith", user.getFullName());
        assertEquals("Senior Developer", user.getBio());
        assertEquals(userId, user.getId());
    }

    @Test
    void testUpdateUserClearBio() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        // Simulate mutation
        user.setBio(null);

        // Verify
        assertNull(user.getBio());
        assertEquals(userId, user.getId());
    }

    // ============================================================================
    // Mutation: updatePost
    // ============================================================================

    @Test
    void testUpdatePostTitle() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Original Title", "Original Content");
        String postId = post.getId();

        // Simulate mutation
        post.setTitle("Updated Title");

        // Verify
        assertEquals("Updated Title", post.getTitle());
        assertEquals(postId, post.getId());
    }

    @Test
    void testUpdatePostContent() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Original Title", "Original Content");
        String postId = post.getId();

        // Simulate mutation
        post.setContent("Updated Content");

        // Verify
        assertEquals("Updated Content", post.getContent());
        assertEquals(postId, post.getId());
    }

    @Test
    void testUpdatePostBothFields() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Original Title", "Original Content");
        String postId = post.getId();

        // Simulate mutation
        post.setTitle("Updated Title");
        post.setContent("Updated Content");

        // Verify
        assertEquals("Updated Title", post.getTitle());
        assertEquals("Updated Content", post.getContent());
        assertEquals(postId, post.getId());
    }

    // ============================================================================
    // Field Immutability
    // ============================================================================

    @Test
    void testUserIdImmutableAfterUpdate() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Bio");
        String originalId = user.getId();

        // Try to "update"
        user.setBio("Updated");

        // Verify ID unchanged
        assertEquals(originalId, user.getId());
    }

    @Test
    void testPostIdImmutableAfterUpdate() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Title", "Content");
        String originalId = post.getId();

        // Try to "update"
        post.setTitle("Updated");

        // Verify ID unchanged
        assertEquals(originalId, post.getId());
    }

    @Test
    void testUsernameImmutable() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        String originalUsername = user.getUsername();

        // Try to "update"
        user.setBio("Updated");

        // Verify username unchanged
        assertEquals(originalUsername, user.getUsername());
    }

    // ============================================================================
    // State Changes
    // ============================================================================

    @Test
    void testSequentialUpdatesAccumulate() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");

        // Apply updates sequentially
        user.setBio("Developer");
        user.setBio("Senior Developer");

        // Verify latest state
        assertEquals("Senior Developer", user.getBio());
    }

    @Test
    void testUpdatesIsolatedBetweenEntities() {
        User user1 = factory.createTestUser("alice", "alice@example.com", "Alice", "Bio1");
        User user2 = factory.createTestUser("bob", "bob@example.com", "Bob", "Bio2");

        String originalBio2 = user2.getBio();

        // Update user1
        user1.setBio("Updated");

        // Verify user2 unchanged
        assertEquals(originalBio2, user2.getBio());
    }

    // ============================================================================
    // Return Value Validation
    // ============================================================================

    @Test
    void testUpdatedUserReturnsAllFields() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        user.setBio("Updated");

        // Verify all fields present
        assertNotNull(user.getId());
        assertEquals("alice", user.getUsername());
        assertEquals("Updated", user.getBio());
    }

    @Test
    void testUpdatedPostReturnsAllFields() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Title", "Content");
        post.setTitle("Updated");

        // Verify all fields present
        assertNotNull(post.getId());
        assertEquals("Updated", post.getTitle());
        assertNotNull(post.getAuthor());
    }

    @Test
    void testMutationMaintainsCreatedAt() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        var originalCreatedAt = user.getCreatedAt();

        // Update
        user.setFullName("Alice Updated");

        // Verify created_at unchanged
        assertEquals(originalCreatedAt, user.getCreatedAt());
    }
}
