package com.fraiseql.graphql;

import com.fraiseql.dto.PostDTO;
import com.fraiseql.dto.UserDTO;
import com.fraiseql.dto.CommentDTO;
import com.fraiseql.service.UserService;
import com.fraiseql.service.PostService;
import com.fraiseql.service.CommentService;
import com.fraiseql.metrics.ApplicationMetrics;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.graphql.data.method.annotation.SchemaMapping;
import org.springframework.stereotype.Controller;

import java.util.List;

@Controller
public class UserGraphQL {

    private final UserService userService;
    private final PostService postService;
    private final CommentService commentService;
    private final ApplicationMetrics metrics;

    public UserGraphQL(UserService userService, PostService postService, CommentService commentService, ApplicationMetrics metrics) {
        this.userService = userService;
        this.postService = postService;
        this.commentService = commentService;
        this.metrics = metrics;
    }

    @QueryMapping
    public UserDTO user(@Argument String id) {
        metrics.incrementGraphQLQueries();
        metrics.recordGraphQLOperation("query", "user");
        return userService.getUserById(id).orElse(null);
    }

    @QueryMapping
    public List<UserDTO> users(@Argument Integer first) {
        metrics.incrementGraphQLQueries();
        metrics.recordGraphQLOperation("query", "users");
        int limit = first != null ? first : 10;
        return userService.getAllUsers(0, limit);
    }

    @SchemaMapping(typeName = "User", field = "posts")
    public List<PostDTO> getUserPosts(UserDTO user) {
        return postService.getPostsByAuthor(user.getId(), 0, 50); // Limit to 50 for performance
    }

    @SchemaMapping(typeName = "User", field = "comments")
    public List<CommentDTO> getUserComments(UserDTO user) {
        return commentService.getCommentsByAuthor(user.getId(), 0, 20); // Limit to 20 for performance
    }
}