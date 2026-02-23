package com.velocitybench;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * In-memory test factory for isolated tests.
 * Thread-safe implementation using ConcurrentHashMap.
 */
public class TestFactory {

    // Data classes
    public static class TestUser {
        public final String id;
        public final int pkUser;
        public final String username;
        public final String fullName;
        public final String bio;
        public final Instant createdAt;
        public final Instant updatedAt;

        public TestUser(String id, int pkUser, String username, String fullName, String bio) {
            this.id = id;
            this.pkUser = pkUser;
            this.username = username;
            this.fullName = fullName;
            this.bio = bio;
            this.createdAt = Instant.now();
            this.updatedAt = Instant.now();
        }
    }

    public static class TestPost {
        public final String id;
        public final int pkPost;
        public final int fkAuthor;
        public final String title;
        public final String content;
        public final Instant createdAt;
        public final Instant updatedAt;
        public final TestUser author;

        public TestPost(String id, int pkPost, int fkAuthor, String title, String content, TestUser author) {
            this.id = id;
            this.pkPost = pkPost;
            this.fkAuthor = fkAuthor;
            this.title = title;
            this.content = content;
            this.author = author;
            this.createdAt = Instant.now();
            this.updatedAt = Instant.now();
        }
    }

    public static class TestComment {
        public final String id;
        public final int pkComment;
        public final int fkPost;
        public final int fkAuthor;
        public final String content;
        public final Instant createdAt;
        public final TestUser author;
        public final TestPost post;

        public TestComment(String id, int pkComment, int fkPost, int fkAuthor, String content, TestUser author, TestPost post) {
            this.id = id;
            this.pkComment = pkComment;
            this.fkPost = fkPost;
            this.fkAuthor = fkAuthor;
            this.content = content;
            this.author = author;
            this.post = post;
            this.createdAt = Instant.now();
        }
    }

    // Storage
    private final Map<String, TestUser> users = new ConcurrentHashMap<>();
    private final Map<String, TestPost> posts = new ConcurrentHashMap<>();
    private final Map<String, TestComment> comments = new ConcurrentHashMap<>();

    private final AtomicInteger userCounter = new AtomicInteger(0);
    private final AtomicInteger postCounter = new AtomicInteger(0);
    private final AtomicInteger commentCounter = new AtomicInteger(0);

    public TestUser createUser(String username, String email, String fullName, String bio) {
        int pk = userCounter.incrementAndGet();
        TestUser user = new TestUser(
            UUID.randomUUID().toString(),
            pk,
            username,
            fullName,
            bio
        );
        users.put(user.id, user);
        return user;
    }

    public TestUser createUser(String username, String email, String fullName) {
        return createUser(username, email, fullName, null);
    }

    public TestPost createPost(String authorId, String title, String content) {
        TestUser author = users.get(authorId);
        if (author == null) {
            throw new RuntimeException("Author not found: " + authorId);
        }

        int pk = postCounter.incrementAndGet();
        TestPost post = new TestPost(
            UUID.randomUUID().toString(),
            pk,
            author.pkUser,
            title,
            content,
            author
        );
        posts.put(post.id, post);
        return post;
    }

    public TestPost createPost(String authorId, String title) {
        return createPost(authorId, title, "Default content");
    }

    public TestComment createComment(String authorId, String postId, String content) {
        TestUser author = users.get(authorId);
        TestPost post = posts.get(postId);

        if (author == null) {
            throw new RuntimeException("Author not found");
        }
        if (post == null) {
            throw new RuntimeException("Post not found");
        }

        int pk = commentCounter.incrementAndGet();
        TestComment comment = new TestComment(
            UUID.randomUUID().toString(),
            pk,
            post.pkPost,
            author.pkUser,
            content,
            author,
            post
        );
        comments.put(comment.id, comment);
        return comment;
    }

    public TestUser getUser(String id) {
        return users.get(id);
    }

    public TestPost getPost(String id) {
        return posts.get(id);
    }

    public TestComment getComment(String id) {
        return comments.get(id);
    }

    public List<TestUser> getAllUsers() {
        return new ArrayList<>(users.values());
    }

    public List<TestPost> getPostsByAuthor(int authorPk) {
        return posts.values().stream()
            .filter(p -> p.fkAuthor == authorPk)
            .collect(Collectors.toList());
    }

    public List<TestComment> getCommentsByPost(int postPk) {
        return comments.values().stream()
            .filter(c -> c.fkPost == postPk)
            .collect(Collectors.toList());
    }

    public void reset() {
        users.clear();
        posts.clear();
        comments.clear();
        userCounter.set(0);
        postCounter.set(0);
        commentCounter.set(0);
    }

    // Utility classes
    public static class ValidationHelper {
        private static final String UUID_REGEX =
            "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$";

        public static boolean isValidUuid(String value) {
            return value != null && value.toLowerCase().matches(UUID_REGEX);
        }
    }

    public static class DataGenerator {
        public static String generateLongString(int length) {
            return "x".repeat(length);
        }

        public static String generateRandomUsername() {
            return "user_" + UUID.randomUUID().toString().substring(0, 8);
        }
    }
}
