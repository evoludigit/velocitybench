package com.velocitybench.graphql;

import com.velocitybench.model.Comment;
import com.velocitybench.model.Post;
import com.velocitybench.model.User;
import graphql.schema.DataFetcher;
import jakarta.inject.Singleton;
import org.dataloader.DataLoader;

import java.util.Collections;
import java.util.List;
import java.util.concurrent.CompletableFuture;

@Singleton
public class TypeResolvers {

    public DataFetcher<CompletableFuture<List<Post>>> userPosts() {
        return env -> {
            User user = env.getSource();
            DataLoader<Integer, List<Post>> loader = env.getDataLoader("postsByAuthorLoader");
            return loader.load(user.pkUser());
        };
    }

    public DataFetcher<List<User>> userFollowers() {
        return env -> Collections.emptyList(); // Not implemented in benchmark schema
    }

    public DataFetcher<List<User>> userFollowing() {
        return env -> Collections.emptyList(); // Not implemented in benchmark schema
    }

    public DataFetcher<CompletableFuture<User>> postAuthor() {
        return env -> {
            Post post = env.getSource();
            DataLoader<Integer, User> loader = env.getDataLoader("userLoader");
            return loader.load(post.fkAuthor());
        };
    }

    public DataFetcher<CompletableFuture<List<Comment>>> postComments() {
        return env -> {
            Post post = env.getSource();
            DataLoader<Integer, List<Comment>> loader = env.getDataLoader("commentsByPostLoader");
            return loader.load(post.pkPost());
        };
    }

    public DataFetcher<CompletableFuture<User>> commentAuthor() {
        return env -> {
            Comment comment = env.getSource();
            DataLoader<Integer, User> loader = env.getDataLoader("userLoader");
            return loader.load(comment.fkAuthor());
        };
    }

    public DataFetcher<CompletableFuture<Post>> commentPost() {
        return env -> {
            Comment comment = env.getSource();
            DataLoader<Integer, Post> loader = env.getDataLoader("postLoader");
            return loader.load(comment.fkPost());
        };
    }
}
