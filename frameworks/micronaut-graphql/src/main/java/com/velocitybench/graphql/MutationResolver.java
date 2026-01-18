package com.velocitybench.graphql;

import com.velocitybench.model.Post;
import com.velocitybench.model.User;
import com.velocitybench.repository.PostRepository;
import com.velocitybench.repository.UserRepository;
import graphql.schema.DataFetcher;
import jakarta.inject.Singleton;

import java.util.Map;

@Singleton
public class MutationResolver {

    private final UserRepository userRepository;
    private final PostRepository postRepository;

    public MutationResolver(UserRepository userRepository, PostRepository postRepository) {
        this.userRepository = userRepository;
        this.postRepository = postRepository;
    }

    public DataFetcher<User> updateUser() {
        return env -> {
            String id = env.getArgument("id");
            Map<String, Object> input = env.getArgument("input");
            String fullName = (String) input.get("fullName");
            String bio = (String) input.get("bio");
            return userRepository.update(id, fullName, bio).orElse(null);
        };
    }

    public DataFetcher<Post> updatePost() {
        return env -> {
            String id = env.getArgument("id");
            Map<String, Object> input = env.getArgument("input");
            String title = (String) input.get("title");
            String content = (String) input.get("content");
            return postRepository.update(id, title, content).orElse(null);
        };
    }
}
