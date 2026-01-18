package com.velocitybench.graphql;

import com.velocitybench.model.Post;
import com.velocitybench.model.User;
import com.velocitybench.repository.PostRepository;
import com.velocitybench.repository.UserRepository;
import graphql.schema.DataFetcher;
import jakarta.inject.Singleton;

import java.util.List;
import java.util.Map;

@Singleton
public class QueryResolver {

    private final UserRepository userRepository;
    private final PostRepository postRepository;

    public QueryResolver(UserRepository userRepository, PostRepository postRepository) {
        this.userRepository = userRepository;
        this.postRepository = postRepository;
    }

    public DataFetcher<String> ping() {
        return env -> "pong";
    }

    public DataFetcher<User> user() {
        return env -> {
            String id = env.getArgument("id");
            return userRepository.findById(id).orElse(null);
        };
    }

    public DataFetcher<List<User>> users() {
        return env -> {
            Integer limit = env.getArgumentOrDefault("limit", 10);
            return userRepository.findAll(Math.min(limit, 100));
        };
    }

    public DataFetcher<Post> post() {
        return env -> {
            String id = env.getArgument("id");
            return postRepository.findById(id).orElse(null);
        };
    }

    public DataFetcher<List<Post>> posts() {
        return env -> {
            Integer limit = env.getArgumentOrDefault("limit", 10);
            return postRepository.findAll(Math.min(limit, 100));
        };
    }
}
