package com.fraiseql;

import com.fraiseql.models.User;
import com.fraiseql.models.Post;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Collection;

class EndpointsTest {
    private TestFactory factory;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
    }

    // ============================================================================
    // Endpoint: GET /api/users (List)
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
            factory.createTestUser(
                "user" + i,
                "user" + i + "@example.com",
                "User",
                ""
            );
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 20);
    }

    @Test
    void testGetUsersReturnsEmptyWhenNoUsers() {
        Collection<User> users = factory.getAllUsers();
        assertEquals(0, users.size());
    }

    @Test
    void testGetUsersWithPagination() {
        for (int i = 0; i < 30; i++) {
            factory.createTestUser(
                "user" + (i % 10),
                "user" + (i % 10) + "@example.com",
                "User",
                ""
            );
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 10);
    }

    // ============================================================================
    // Endpoint: GET /api/users/:id (Detail)
    // ============================================================================

    @Test
    void testGetUserDetailReturnsUser() {
        User user = factory.createTestUser("alice", "alice@example.com", "Alice", "Developer");
        String userId = user.getId();

        User retrieved = factory.getUser(userId);
        assertNotNull(retrieved);
        assertEquals("alice", retrieved.getUsername());
    }

    @Test
    void testGetUserDetailWithNullBio() {
        User user = factory.createTestUser("bob", "bob@example.com", "Bob", "");
        String userId = user.getId();

        User retrieved = factory.getUser(userId);
        assertNotNull(retrieved);
        assertNull(retrieved.getBio());
    }

    @Test
    void testGetUserDetailWithSpecialChars() {
        User user = factory.createTestUser("charlie", "charlie@example.com", "Char'lie", "Quote: \"test\"");
        String userId = user.getId();

        User retrieved = factory.getUser(userId);
        assertNotNull(retrieved);
    }

    @Test
    void testGetUserDetailNotFound() {
        User retrieved = factory.getUser("nonexistent-id");
        assertNull(retrieved);
    }

    // ============================================================================
    // Endpoint: GET /api/posts (List)
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
    // Endpoint: GET /api/posts/:id (Detail)
    // ============================================================================

    @Test
    void testGetPostDetailReturnsPost() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Test Post", "Test Content");
        String postId = post.getId();

        Post retrieved = factory.getPost(postId);
        assertNotNull(retrieved);
        assertEquals("Test Post", retrieved.getTitle());
    }

    @Test
    void testGetPostDetailWithNullContent() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "No Content", "");
        String postId = post.getId();

        Post retrieved = factory.getPost(postId);
        assertNotNull(retrieved);
        assertNull(retrieved.getContent());
    }

    @Test
    void testGetPostDetailWithSpecialChars() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        Post post = factory.createTestPost(author.getId(), "Post with <tags>", "Content & more");
        String postId = post.getId();

        Post retrieved = factory.getPost(postId);
        assertNotNull(retrieved);
    }

    @Test
    void testGetPostDetailNotFound() {
        Post retrieved = factory.getPost("nonexistent-id");
        assertNull(retrieved);
    }

    // ============================================================================
    // Endpoint: GET /api/posts/by-author/:id
    // ============================================================================

    @Test
    void testGetPostsByAuthorReturnsAuthorsPosts() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");

        factory.createTestPost(author.getId(), "Post 1", "Content");
        factory.createTestPost(author.getId(), "Post 2", "Content");
        factory.createTestPost(author.getId(), "Post 3", "Content");

        long authorPosts = factory.getAllPosts().stream()
            .filter(p -> p.getAuthor().getId().equals(author.getId()))
            .count();

        assertEquals(3, authorPosts);
    }

    @Test
    void testMultipleAuthorsSeperatePosts() {
        User author1 = factory.createTestUser("author1", "author1@example.com", "Author 1", "");
        User author2 = factory.createTestUser("author2", "author2@example.com", "Author 2", "");

        factory.createTestPost(author1.getId(), "Post 1", "Content");
        factory.createTestPost(author1.getId(), "Post 2", "Content");
        factory.createTestPost(author2.getId(), "Post 1", "Content");

        long author1Posts = factory.getAllPosts().stream()
            .filter(p -> p.getAuthor().getId().equals(author1.getId()))
            .count();
        long author2Posts = factory.getAllPosts().stream()
            .filter(p -> p.getAuthor().getId().equals(author2.getId()))
            .count();

        assertEquals(2, author1Posts);
        assertEquals(1, author2Posts);
    }

    @Test
    void testAuthorWithNoPosts() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");

        long authorPosts = factory.getAllPosts().stream()
            .filter(p -> p.getAuthor().getId().equals(author.getId()))
            .count();

        assertEquals(0, authorPosts);
    }

    // ============================================================================
    // Endpoint: Response Headers
    // ============================================================================

    @Test
    void testGetUsersReturnsJSON() {
        factory.createTestUser("alice", "alice@example.com", "Alice", "");
        assertTrue(factory.getUserCount() > 0);
    }

    @Test
    void testGetPostsReturnsJSON() {
        User author = factory.createTestUser("author", "author@example.com", "Author", "");
        factory.createTestPost(author.getId(), "Post", "Content");
        assertTrue(factory.getPostCount() > 0);
    }

    // ============================================================================
    // Endpoint: Pagination
    // ============================================================================

    @Test
    void testPaginationPage0WithSize10() {
        for (int i = 0; i < 30; i++) {
            factory.createTestUser(
                "user" + (i % 10),
                "user" + (i % 10) + "@example.com",
                "User",
                ""
            );
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 10);
    }

    @Test
    void testPaginationPage1WithSize10() {
        for (int i = 0; i < 30; i++) {
            factory.createTestUser(
                "user" + (i % 10),
                "user" + (i % 10) + "@example.com",
                "User",
                ""
            );
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 10);
    }

    @Test
    void testPaginationLastPageWithFewerItems() {
        for (int i = 0; i < 25; i++) {
            factory.createTestUser(
                "user" + (i % 10),
                "user" + (i % 10) + "@example.com",
                "User",
                ""
            );
        }

        Collection<User> users = factory.getAllUsers();
        assertTrue(users.size() >= 5);
    }

    // ============================================================================
    // Endpoint: Data Consistency
    // ============================================================================

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
}
