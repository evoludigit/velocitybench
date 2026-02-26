package com.fraiseql;

import com.fraiseql.entities.User;
import com.fraiseql.entities.Post;
import com.fraiseql.entities.Comment;
import java.time.LocalDateTime;
import java.util.*;

public class TestFactory {
    private final Map<String, User> users = new HashMap<>();
    private final Map<String, Post> posts = new HashMap<>();
    private int userCounter = 1;
    private int postCounter = 1;

    public TestFactory() {
    }

    public User createTestUser(String username, String email, String fullName, String bio) {
        User user = new User();
        user.setId(UUID.randomUUID().toString());
        user.setPkUser(userCounter++);
        user.setUsername(username);
        user.setFullName(fullName);
        user.setBio(bio == null || bio.isEmpty() ? null : bio);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        users.put(user.getId(), user);
        return user;
    }

    public Post createTestPost(String authorId, String title, String content) {
        User author = users.get(authorId);
        if (author == null) {
            throw new IllegalArgumentException("Author not found: " + authorId);
        }

        Post post = new Post();
        post.setId(UUID.randomUUID().toString());
        post.setPkPost(postCounter++);
        post.setTitle(title);
        post.setContent(content == null || content.isEmpty() ? "" : content);
        post.setFkAuthor(author.getPkUser());
        post.setCreatedAt(LocalDateTime.now());
        post.setUpdatedAt(LocalDateTime.now());

        posts.put(post.getId(), post);
        return post;
    }

    public Comment createTestComment(String authorId, String postId, String content) {
        User author = users.get(authorId);
        Post post = posts.get(postId);

        if (author == null || post == null) {
            throw new IllegalArgumentException("Author or Post not found");
        }

        Comment comment = new Comment();
        comment.setId(UUID.randomUUID().toString());
        comment.setContent(content);
        comment.setFkAuthor(author.getPkUser());
        comment.setFkPost(post.getPkPost());
        comment.setCreatedAt(LocalDateTime.now());

        return comment;
    }

    public User getUser(String id) {
        return users.get(id);
    }

    public Post getPost(String id) {
        return posts.get(id);
    }

    public Collection<User> getAllUsers() {
        return users.values();
    }

    public Collection<Post> getAllPosts() {
        return posts.values();
    }

    public int getUserCount() {
        return users.size();
    }

    public int getPostCount() {
        return posts.size();
    }

    public void reset() {
        users.clear();
        posts.clear();
        userCounter = 1;
        postCounter = 1;
    }
}
