package com.fraiseql.graphql;

import com.fraiseql.dto.PostDTO;
import com.fraiseql.dto.UserDTO;
import com.fraiseql.dto.CommentDTO;
import com.fraiseql.service.PostService;
import com.fraiseql.service.UserService;
import com.fraiseql.service.CommentService;
import com.fraiseql.metrics.ApplicationMetrics;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.graphql.data.method.annotation.SchemaMapping;
import org.springframework.stereotype.Controller;

import java.util.List;

@Controller
public class PostGraphQL {

    private final PostService postService;
    private final UserService userService;
    private final CommentService commentService;
    private final ApplicationMetrics metrics;

    public PostGraphQL(PostService postService, UserService userService, CommentService commentService, ApplicationMetrics metrics) {
        this.postService = postService;
        this.userService = userService;
        this.commentService = commentService;
        this.metrics = metrics;
    }

    @QueryMapping
    public PostDTO post(@Argument String id) {
        metrics.incrementGraphQLQueries();
        metrics.recordGraphQLOperation("query", "post");
        return postService.getPostById(id).orElse(null);
    }

    @QueryMapping
    public List<PostDTO> posts(@Argument Integer first) {
        metrics.incrementGraphQLQueries();
        metrics.recordGraphQLOperation("query", "posts");
        int limit = first != null ? first : 10;
        return postService.getAllPosts(0, limit);
    }

    @QueryMapping
    public List<PostDTO> postsByUser(@Argument String userId, @Argument Integer first) {
        metrics.incrementGraphQLQueries();
        metrics.recordGraphQLOperation("query", "postsByUser");
        int limit = first != null ? first : 10;
        return postService.getPostsByAuthor(userId, 0, limit);
    }

    @SchemaMapping(typeName = "Post", field = "author")
    public UserDTO getPostAuthor(PostDTO post) {
        return userService.getUserById(post.getAuthorId()).orElse(null);
    }

    @SchemaMapping(typeName = "Post", field = "comments")
    public List<CommentDTO> getPostComments(PostDTO post) {
        return commentService.getCommentsByPost(post.getId(), 0, 50); // Limit to 50 for performance
    }
}