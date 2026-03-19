package com.velocitybench.graphql;

import com.velocitybench.model.Comment;
import com.velocitybench.model.Post;
import com.velocitybench.model.User;
import com.velocitybench.repository.CommentRepository;
import com.velocitybench.repository.PostRepository;
import com.velocitybench.repository.UserRepository;
import io.smallrye.graphql.api.Context;
import jakarta.inject.Inject;
import org.eclipse.microprofile.graphql.*;

import java.util.*;

@GraphQLApi
public class GraphQLResource {

    @Inject
    UserRepository userRepository;

    @Inject
    PostRepository postRepository;

    @Inject
    CommentRepository commentRepository;

    @Inject
    Context context;

    // Queries
    @Query
    public String ping() {
        return "pong";
    }

    @Query
    public User user(@Name("id") String id) {
        return userRepository.findById(id).orElse(null);
    }

    @Query
    public List<User> users(@DefaultValue("10") @Name("limit") int limit) {
        return userRepository.findAll(Math.min(limit, 100));
    }

    @Query
    public Post post(@Name("id") String id) {
        return postRepository.findById(id).orElse(null);
    }

    @Query
    public List<Post> posts(@DefaultValue("10") @Name("limit") int limit) {
        return postRepository.findAll(Math.min(limit, 100));
    }

    @Query
    public List<Comment> comments(@DefaultValue("20") @Name("limit") int limit) {
        return commentRepository.findAll(Math.min(limit, 100));
    }

    // Mutations
    @Mutation
    public User updateUser(@Name("id") String id, @Name("input") UpdateUserInput input) {
        return userRepository.update(id, input.fullName, input.bio).orElse(null);
    }

    @Mutation
    public Post updatePost(@Name("id") String id, @Name("input") UpdatePostInput input) {
        return postRepository.update(id, input.title, input.content).orElse(null);
    }

    // Field resolvers for User
    public List<Post> posts(@Source User user, @DefaultValue("50") @Name("limit") int limit) {
        // Note: In production, use DataLoader for batching
        Map<Integer, List<Post>> result = postRepository.findByAuthorPks(Set.of(user.getPkUser()), Math.min(limit, 50));
        return result.getOrDefault(user.getPkUser(), Collections.emptyList());
    }

    public List<User> followers(@Source User user, @DefaultValue("50") @Name("limit") int limit) {
        return Collections.emptyList(); // Not implemented in benchmark schema
    }

    public List<User> following(@Source User user, @DefaultValue("50") @Name("limit") int limit) {
        return Collections.emptyList(); // Not implemented in benchmark schema
    }

    // Field resolvers for Post
    public User author(@Source Post post) {
        Map<Integer, User> users = userRepository.findByPks(Set.of(post.getFkAuthor()));
        return users.get(post.getFkAuthor());
    }

    public List<Comment> comments(@Source Post post, @DefaultValue("50") @Name("limit") int limit) {
        Map<Integer, List<Comment>> result = commentRepository.findByPostPks(Set.of(post.getPkPost()), Math.min(limit, 50));
        return result.getOrDefault(post.getPkPost(), Collections.emptyList());
    }

    // Field resolvers for Comment
    public User author(@Source Comment comment) {
        Map<Integer, User> users = userRepository.findByPks(Set.of(comment.getFkAuthor()));
        return users.get(comment.getFkAuthor());
    }

    public Post post(@Source Comment comment) {
        Map<Integer, Post> posts = postRepository.findByPks(Set.of(comment.getFkPost()));
        return posts.get(comment.getFkPost());
    }

    // Input types
    public static class UpdateUserInput {
        public String fullName;
        public String bio;
    }

    public static class UpdatePostInput {
        public String title;
        public String content;
    }
}
