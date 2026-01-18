package com.fraiseql;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Comprehensive test suite for Spring Boot ORM (Naive) resolvers.
 * Uses in-memory TestFactory for fast, isolated tests.
 */
class ResolverTest {

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
    // User Query Tests
    // ============================================================================

    @Test
    void testQueryUserByUuid() {
        var user = factory.createUser("alice", "alice@example.com", "Alice Smith", "Hello!");

        var result = factory.getUser(user.id);

        assertNotNull(result);
        assertEquals(user.id, result.id);
        assertEquals("alice", result.username);
        assertEquals("Alice Smith", result.fullName);
        assertEquals("Hello!", result.bio);
    }

    @Test
    void testQueryUsersReturnsList() {
        factory.createUser("alice", "alice@example.com", "Alice");
        factory.createUser("bob", "bob@example.com", "Bob");
        factory.createUser("charlie", "charlie@example.com", "Charlie");

        List<TestFactory.TestUser> users = factory.getAllUsers();

        assertEquals(3, users.size());
    }

    @Test
    void testQueryUserNotFound() {
        var result = factory.getUser("non-existent-id");

        assertNull(result);
    }

    // ============================================================================
    // Post Query Tests
    // ============================================================================

    @Test
    void testQueryPostById() {
        var user = factory.createUser("author", "author@example.com", "Author");
        var post = factory.createPost(user.id, "Test Post", "Test content");

        var result = factory.getPost(post.id);

        assertNotNull(result);
        assertEquals("Test Post", result.title);
        assertEquals("Test content", result.content);
    }

    @Test
    void testQueryPostsByAuthor() {
        var user = factory.createUser("author", "author@example.com", "Author");
        factory.createPost(user.id, "Post 1", "Content 1");
        factory.createPost(user.id, "Post 2", "Content 2");

        var posts = factory.getPostsByAuthor(user.pkUser);

        assertEquals(2, posts.size());
    }

    // ============================================================================
    // Comment Query Tests
    // ============================================================================

    @Test
    void testQueryCommentById() {
        var author = factory.createUser("author", "author@example.com", "Author");
        var post = factory.createPost(author.id, "Test Post", "Content");
        var commenter = factory.createUser("commenter", "commenter@example.com", "Commenter");
        var comment = factory.createComment(commenter.id, post.id, "Great post!");

        var result = factory.getComment(comment.id);

        assertNotNull(result);
        assertEquals("Great post!", result.content);
    }

    @Test
    void testQueryCommentsByPost() {
        var author = factory.createUser("author", "author@example.com", "Author");
        var post = factory.createPost(author.id, "Test Post", "Content");
        var commenter = factory.createUser("commenter", "commenter@example.com", "Commenter");
        factory.createComment(commenter.id, post.id, "Comment 1");
        factory.createComment(commenter.id, post.id, "Comment 2");

        var comments = factory.getCommentsByPost(post.pkPost);

        assertEquals(2, comments.size());
    }

    // ============================================================================
    // Relationship Tests
    // ============================================================================

    @Test
    void testUserPostsRelationship() {
        var user = factory.createUser("author", "author@example.com", "Author");
        var post1 = factory.createPost(user.id, "Post 1", "Content 1");
        var post2 = factory.createPost(user.id, "Post 2", "Content 2");

        var posts = factory.getPostsByAuthor(user.pkUser);

        assertEquals(2, posts.size());
        var postIds = posts.stream().map(p -> p.id).collect(Collectors.toList());
        assertTrue(postIds.contains(post1.id));
        assertTrue(postIds.contains(post2.id));
    }

    @Test
    void testPostAuthorRelationship() {
        var author = factory.createUser("author", "author@example.com", "Author");
        var post = factory.createPost(author.id, "Test Post", "Content");

        assertNotNull(post.author);
        assertEquals(author.pkUser, post.author.pkUser);
    }

    @Test
    void testCommentAuthorRelationship() {
        var author = factory.createUser("author", "author@example.com", "Author");
        var post = factory.createPost(author.id, "Test Post", "Content");
        var commenter = factory.createUser("commenter", "commenter@example.com", "Commenter");
        var comment = factory.createComment(commenter.id, post.id, "Great!");

        assertNotNull(comment.author);
        assertEquals(commenter.pkUser, comment.author.pkUser);
    }

    // ============================================================================
    // Edge Case Tests
    // ============================================================================

    @Test
    void testNullBio() {
        var user = factory.createUser("user", "user@example.com", "User");

        assertNull(user.bio);
    }

    @Test
    void testEmptyPostsList() {
        var user = factory.createUser("newuser", "new@example.com", "New User");

        var posts = factory.getPostsByAuthor(user.pkUser);

        assertTrue(posts.isEmpty());
    }

    @Test
    void testSpecialCharactersInContent() {
        var user = factory.createUser("author", "author@example.com", "Author");
        String specialContent = "Test with 'quotes' and \"double quotes\" and <html>";
        var post = factory.createPost(user.id, "Special", specialContent);

        assertEquals(specialContent, post.content);
    }

    @Test
    void testUnicodeContent() {
        var user = factory.createUser("author", "author@example.com", "Author");
        String unicodeContent = "Test with émojis \uD83C\uDF89 and ñ and 中文";
        var post = factory.createPost(user.id, "Unicode", unicodeContent);

        assertEquals(unicodeContent, post.content);
    }

    // ============================================================================
    // Performance Tests
    // ============================================================================

    @Test
    void testCreateManyPosts() {
        var user = factory.createUser("author", "author@example.com", "Author");

        for (int i = 0; i < 50; i++) {
            factory.createPost(user.id, "Post " + i, "Content");
        }

        var posts = factory.getPostsByAuthor(user.pkUser);
        assertEquals(50, posts.size());
    }

    @Test
    void testReset() {
        factory.createUser("user1", "user1@example.com", "User 1");
        factory.createUser("user2", "user2@example.com", "User 2");

        factory.reset();

        assertTrue(factory.getAllUsers().isEmpty());
    }

    // ============================================================================
    // Validation Tests
    // ============================================================================

    @Test
    void testValidUuid() {
        var user = factory.createUser("user", "user@example.com", "User");

        assertTrue(TestFactory.ValidationHelper.isValidUuid(user.id));
    }

    @Test
    void testCreatePostWithInvalidAuthor() {
        Exception exception = assertThrows(RuntimeException.class, () -> {
            factory.createPost("invalid-author", "Test", "Content");
        });

        assertTrue(exception.getMessage().contains("Author not found"));
    }

    @Test
    void testCreateCommentWithInvalidPost() {
        var user = factory.createUser("user", "user@example.com", "User");

        Exception exception = assertThrows(RuntimeException.class, () -> {
            factory.createComment(user.id, "invalid-post", "Content");
        });

        assertTrue(exception.getMessage().contains("Post not found"));
    }

    @Test
    void testLongContent() {
        var user = factory.createUser("author", "author@example.com", "Author");
        String longContent = TestFactory.DataGenerator.generateLongString(100000);
        var post = factory.createPost(user.id, "Long", longContent);

        assertEquals(100000, post.content.length());
    }
}
