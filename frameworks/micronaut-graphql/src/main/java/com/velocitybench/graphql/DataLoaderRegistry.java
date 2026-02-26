package com.velocitybench.graphql;

import com.velocitybench.model.Comment;
import com.velocitybench.model.Post;
import com.velocitybench.model.User;
import com.velocitybench.repository.CommentRepository;
import com.velocitybench.repository.PostRepository;
import com.velocitybench.repository.UserRepository;
import jakarta.inject.Singleton;
import org.dataloader.BatchLoader;
import org.dataloader.DataLoader;
import org.dataloader.DataLoaderOptions;

import java.util.*;
import java.util.concurrent.CompletableFuture;

@Singleton
public class DataLoaderRegistry {

    private final UserRepository userRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;

    public DataLoaderRegistry(UserRepository userRepository, PostRepository postRepository, CommentRepository commentRepository) {
        this.userRepository = userRepository;
        this.postRepository = postRepository;
        this.commentRepository = commentRepository;
    }

    public org.dataloader.DataLoaderRegistry create() {
        org.dataloader.DataLoaderRegistry registry = new org.dataloader.DataLoaderRegistry();

        registry.register("userLoader", createUserLoader());
        registry.register("postLoader", createPostLoader());
        registry.register("postsByAuthorLoader", createPostsByAuthorLoader());
        registry.register("commentsByPostLoader", createCommentsByPostLoader());

        return registry;
    }

    private DataLoader<Integer, User> createUserLoader() {
        BatchLoader<Integer, User> batchLoader = keys -> CompletableFuture.supplyAsync(() -> {
            Map<Integer, User> users = userRepository.findByPks(new HashSet<>(keys));
            return keys.stream().map(users::get).toList();
        });
        return DataLoader.newDataLoader(batchLoader, DataLoaderOptions.newOptions().setCachingEnabled(true));
    }

    private DataLoader<Integer, Post> createPostLoader() {
        BatchLoader<Integer, Post> batchLoader = keys -> CompletableFuture.supplyAsync(() -> {
            Map<Integer, Post> posts = postRepository.findByPks(new HashSet<>(keys));
            return keys.stream().map(posts::get).toList();
        });
        return DataLoader.newDataLoader(batchLoader, DataLoaderOptions.newOptions().setCachingEnabled(true));
    }

    private DataLoader<Integer, List<Post>> createPostsByAuthorLoader() {
        BatchLoader<Integer, List<Post>> batchLoader = keys -> CompletableFuture.supplyAsync(() -> {
            Map<Integer, List<Post>> postsByAuthor = postRepository.findByAuthorPks(new HashSet<>(keys), 50);
            return keys.stream().map(k -> postsByAuthor.getOrDefault(k, Collections.emptyList())).toList();
        });
        return DataLoader.newDataLoader(batchLoader, DataLoaderOptions.newOptions().setCachingEnabled(true));
    }

    private DataLoader<Integer, List<Comment>> createCommentsByPostLoader() {
        BatchLoader<Integer, List<Comment>> batchLoader = keys -> CompletableFuture.supplyAsync(() -> {
            Map<Integer, List<Comment>> commentsByPost = commentRepository.findByPostPks(new HashSet<>(keys), 50);
            return keys.stream().map(k -> commentsByPost.getOrDefault(k, Collections.emptyList())).toList();
        });
        return DataLoader.newDataLoader(batchLoader, DataLoaderOptions.newOptions().setCachingEnabled(true));
    }
}
