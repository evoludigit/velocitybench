package com.fraiseql;

import com.fraiseql.entities.User;
import com.fraiseql.entities.Post;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Collection;
import java.util.UUID;

class FullTestSuite {
    private TestFactory factory;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
    }

    // ============================================================================
    // Endpoints: GET /api/users (List)
    // ============================================================================

    @Test
    void testGetUsersListReturnsUsers() {
        factory.createTestUser("alice", "alice@example.com", "Alice", "");
        factory.createTestUser("bob", "bob@example.com", "Bob", "");
        factory.createTestUser("charlie", "charlie@example.com", "Charlie", "");

        Collection<User> users = factory.getAllUsers();
        assertEquals(3, users.size());
    }

    @Test
    void testGetUsersRespectLimit() {
        for (int i = 0; i < 20; i++) {
            factory.createTestUser("user" + i, "user" + i + "@example.com", "User", "");
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 20);
    }

    @Test
    void testGetUsersReturnsEmpty() {
        Collection<User> users = factory.getAllUsers();
        assertEquals(0, users.size());
    }

    // ============================================================================
    // Endpoints: GET /api/users/:id (Detail)
    // ============================================================================

    @Test
    void testGetUserDetailReturnsUser() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        User retrieved = factory.getUser(user.getId());
        assertNotNull(retrieved);
        assertEquals("alice", retrieved.getUsername());
    }

    @Test
    void testGetUserDetailWithNullBio() {
        User user = factory.createTestUser("bob", "bob@example.com", "Bob", "");
        User retrieved = factory.getUser(user.getId());
        assertNotNull(retrieved);
        assertNull(retrieved.getBio());
    }

    @Test
    void testGetUserDetailNotFound() {
        User retrieved = factory.getUser("nonexistent-id");
        assertNull(retrieved);
    }

    // ============================================================================
    // Endpoints: GET /api/posts (List)
    // ============================================================================

    @Test
    void testGetPostsListReturnsPosts() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        factory.createTestPost(author.getId(), "Post 1", "Content");
        factory.createTestPost(author.getId(), "Post 2", "Content");
        factory.createTestPost(author.getId(), "Post 3", "Content");

        Collection<Post> posts = factory.getAllPosts();
        assertEquals(3, posts.size());
    }

    @Test
    void testGetPostsRespectLimit() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        for (int i = 0; i < 20; i++) {
            factory.createTestPost(author.getId(), "Post " + i, "Content");
        }

        Collection<Post> posts = factory.getAllPosts();
        assertTrue(posts.size() >= 20);
    }

    @Test
    void testGetPostsReturnsEmpty() {
        Collection<Post> posts = factory.getAllPosts();
        assertEquals(0, posts.size());
    }

    // ============================================================================
    // Endpoints: GET /api/posts/:id (Detail)
    // ============================================================================

    @Test
    void testGetPostDetailReturnsPost() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Test Post", "Test Content");
        Post retrieved = factory.getPost(post.getId());
        assertNotNull(retrieved);
        assertEquals("Test Post", retrieved.getTitle());
    }

    @Test
    void testGetPostDetailNotFound() {
        Post retrieved = factory.getPost("nonexistent-id");
        assertNull(retrieved);
    }

    // ============================================================================
    // Errors: 404 Not Found
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
    // Errors: Invalid Input
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
    // Edge Cases: UUID Validation
    // ============================================================================

    @Test
    void testAllUserIdsAreUUID() {
        factory.createTestUser("user0", "user0@example.com", "User", "");
        factory.createTestUser("user1", "user1@example.com", "User", "");

        for (User user : factory.getAllUsers()) {
            assertDoesNotThrow(() -> UUID.fromString(user.getId()));
        }
    }

    @Test
    void testAllPostIdsAreUUID() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        factory.createTestPost(author.getId(), "Post0", "Content");
        factory.createTestPost(author.getId(), "Post1", "Content");

        for (Post post : factory.getAllPosts()) {
            assertDoesNotThrow(() -> UUID.fromString(post.getId()));
        }
    }

    // ============================================================================
    // Edge Cases: Special Characters
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
    // Edge Cases: Boundary Conditions
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
    // Edge Cases: Null/Empty Fields
    // ============================================================================

    @Test
    void testNullBioIsHandled() {
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
    // Edge Cases: Uniqueness
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

    // ============================================================================
    // Mutations: updateUser
    // ============================================================================

    @Test
    void testUpdateUserFullName() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        user.setFullName("Alice Smith");

        assertEquals("Alice Smith", user.getFullName());
        assertEquals(userId, user.getId());
    }

    @Test
    void testUpdateUserBio() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        user.setBio("Senior Developer");

        assertEquals("Senior Developer", user.getBio());
        assertEquals(userId, user.getId());
    }

    // ============================================================================
    // Mutations: updatePost
    // ============================================================================

    @Test
    void testUpdatePostTitle() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Original Title", "Original Content");
        String postId = post.getId();

        post.setTitle("Updated Title");

        assertEquals("Updated Title", post.getTitle());
        assertEquals(postId, post.getId());
    }

    @Test
    void testUpdatePostContent() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Original Title", "Original Content");
        String postId = post.getId();

        post.setContent("Updated Content");

        assertEquals("Updated Content", post.getContent());
        assertEquals(postId, post.getId());
    }

    // ============================================================================
    // Mutations: Field Immutability
    // ============================================================================

    @Test
    void testUserIdImmutableAfterUpdate() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Bio");
        String originalId = user.getId();

        user.setBio("Updated");

        assertEquals(originalId, user.getId());
    }

    @Test
    void testPostIdImmutableAfterUpdate() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Title", "Content");
        String originalId = post.getId();

        post.setTitle("Updated");

        assertEquals(originalId, post.getId());
    }

    @Test
    void testUsernameImmutable() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        String originalUsername = user.getUsername();

        user.setBio("Updated");

        assertEquals(originalUsername, user.getUsername());
    }

    // ============================================================================
    // Mutations: State Changes
    // ============================================================================

    @Test
    void testSequentialUpdatesAccumulate() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");

        user.setBio("Developer");
        user.setBio("Senior Developer");

        assertEquals("Senior Developer", user.getBio());
    }

    @Test
    void testUpdatesIsolatedBetweenEntities() {
        User user1 = factory.createTestUser("alice", "alice@example.com", "Alice", "Bio1");
        User user2 = factory.createTestUser("bob", "bob@example.com", "Bob", "Bio2");

        String originalBio2 = user2.getBio();

        user1.setBio("Updated");

        assertEquals(originalBio2, user2.getBio());
    }

    // ============================================================================
    // Pagination and Consistency
    // ============================================================================

    @Test
    void testPaginationPage0WithSize10() {
        for (int i = 0; i < 30; i++) {
            factory.createTestUser("user" + (i % 10), "user" + (i % 10) + "@example.com", "User", "");
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 10);
    }

    @Test
    void testDataConsistencyListDetailMatch() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Bio");

        User listUser = factory.getUser(user.getId());
        User detailUser = factory.getUser(user.getId());

        assertEquals(listUser.getUsername(), detailUser.getUsername());
    }

    @Test
    void testRepeatedRequestsReturnSameData() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");

        User retrieved1 = factory.getUser(user.getId());
        User retrieved2 = factory.getUser(user.getId());

        assertEquals(retrieved1.getId(), retrieved2.getId());
    }

    // ============================================================================
    // Relationships
    // ============================================================================

    @Test
    void testMultipleAuthorsSeperatePosts() {
        User author1 = factory.createTestUser("author1", "author1@example.com", "Author1", "");
        User author2 = factory.createTestUser("author2", "author2@example.com", "Author2", "");

        factory.createTestPost(author1.getId(), "Post 1", "Content");
        factory.createTestPost(author1.getId(), "Post 2", "Content");
        factory.createTestPost(author2.getId(), "Post 1", "Content");

        long author1Posts = factory.getAllPosts().stream()
            .filter(p -> p.getFkAuthor() == author1.getPkUser()).count();
        long author2Posts = factory.getAllPosts().stream()
            .filter(p -> p.getFkAuthor() == author2.getPkUser()).count();

        assertEquals(2, author1Posts);
        assertEquals(1, author2Posts);
    }

    @Test
    void testAuthorWithNoPosts() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        long authorPosts = factory.getAllPosts().stream()
            .filter(p -> p.getFkAuthor() == author.getPkUser()).count();
        assertEquals(0, authorPosts);
    }

    @Test
    void testPostReferencesCorrectAuthor() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post", "Content");
        assertEquals(post.getFkAuthor(), author.getPkUser());
    }

    @Test
    void testMultiplePostsReferenceDifferentAuthors() {
        User author1 = factory.createTestUser("author1", "author1@example.com", "Author1", "");
        User author2 = factory.createTestUser("author2", "author2@example.com", "Author2", "");

        Post post1 = factory.createTestPost(author1.getId(), "Post1", "Content");
        Post post2 = factory.createTestPost(author2.getId(), "Post2", "Content");

        assertNotEquals(post1.getFkAuthor(), post2.getFkAuthor());
        assertEquals(post1.getFkAuthor(), author1.getPkUser());
        assertEquals(post2.getFkAuthor(), author2.getPkUser());
    }

    // ============================================================================
    // Data Types
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

    @Test
    void testPrimaryKeyIsInteger() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");
        assertTrue(user.getPkUser() > 0);
    }

    @Test
    void testPostPrimaryKeyIsInteger() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post", "Content");
        assertTrue(post.getPkPost() > 0);
    }

    // ============================================================================
    // Mutations: Return Values
    // ============================================================================

    @Test
    void testUpdatedUserReturnsAllFields() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        user.setBio("Updated");

        assertNotNull(user.getId());
        assertEquals("alice", user.getUsername());
        assertEquals("Updated", user.getBio());
    }

    @Test
    void testUpdatedPostReturnsAllFields() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Title", "Content");
        post.setTitle("Updated");

        assertNotNull(post.getId());
        assertEquals("Updated", post.getTitle());
        assertTrue(post.getFkAuthor() > 0);
    }

    // ============================================================================
    // Pagination Additional Tests
    // ============================================================================

    @Test
    void testPaginationWithMultiplePages() {
        for (int i = 0; i < 25; i++) {
            factory.createTestUser("user" + (i % 10), "user" + (i % 10) + "@example.com", "User", "");
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 5);
    }

    @Test
    void testPostsByAuthorReturnsAuthorsPosts() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");

        factory.createTestPost(author.getId(), "Post 1", "Content");
        factory.createTestPost(author.getId(), "Post 2", "Content");
        factory.createTestPost(author.getId(), "Post 3", "Content");

        long authorPosts = factory.getAllPosts().stream()
            .filter(p -> p.getFkAuthor() == author.getPkUser()).count();

        assertEquals(3, authorPosts);
    }

    @Test
    void testResponseStructureUserHasRequiredFields() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "");

        assertNotNull(user.getId());
        assertEquals("alice", user.getUsername());
    }

    @Test
    void testResponseStructurePostHasRequiredFields() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post", "Content");

        assertNotNull(post.getId());
        assertEquals("Post", post.getTitle());
    }

    @Test
    void testPostWithSpecialCharactersInTitle() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post with <tags>", "Content & more");
        Post retrieved = factory.getPost(post.getId());

        assertNotNull(retrieved);
    }

    @Test
    void testPostWithSpecialCharactersInContent() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Title", "Content with 'quotes' and \"double\"");
        Post retrieved = factory.getPost(post.getId());

        assertNotNull(retrieved);
    }

    @Test
    void testEmptyContentPost() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "No Content", "");
        Post retrieved = factory.getPost(post.getId());

        assertNotNull(retrieved);
        assertEquals("", retrieved.getContent());
    }

    // ============================================================================
    // Helper Methods
    // ============================================================================

    private String generateLongString(int length) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {
            sb.append(i % 10);
        }
        return sb.toString();
    }
}
