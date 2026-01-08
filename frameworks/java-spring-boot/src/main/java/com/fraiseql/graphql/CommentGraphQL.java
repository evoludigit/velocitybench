package com.fraiseql.graphql;

import com.fraiseql.dto.CommentDTO;
import com.fraiseql.dto.UserDTO;
import com.fraiseql.dto.PostDTO;
import com.fraiseql.service.CommentService;
import com.fraiseql.service.UserService;
import com.fraiseql.service.PostService;
import com.fraiseql.metrics.ApplicationMetrics;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.graphql.data.method.annotation.SchemaMapping;
import org.springframework.stereotype.Controller;

import java.util.List;

@Controller
public class CommentGraphQL {

    private final CommentService commentService;
    private final UserService userService;
    private final PostService postService;
    private final ApplicationMetrics metrics;

    public CommentGraphQL(CommentService commentService, UserService userService, PostService postService, ApplicationMetrics metrics) {
        this.commentService = commentService;
        this.userService = userService;
        this.postService = postService;
        this.metrics = metrics;
    }

    @QueryMapping
    public List<CommentDTO> commentsByPost(@Argument String postId, @Argument Integer first) {
        metrics.incrementGraphQLQueries();
        metrics.recordGraphQLOperation("query", "commentsByPost");
        int limit = first != null ? first : 10;
        return commentService.getCommentsByPost(postId, 0, limit);
    }

    @SchemaMapping(typeName = "Comment", field = "author")
    public UserDTO getCommentAuthor(CommentDTO comment) {
        return userService.getUserById(comment.getAuthorId()).orElse(null);
    }

    @SchemaMapping(typeName = "Comment", field = "post")
    public PostDTO getCommentPost(CommentDTO comment) {
        return postService.getPostById(comment.getPostId()).orElse(null);
    }

    @SchemaMapping(typeName = "Comment", field = "parent")
    public CommentDTO getCommentParent(CommentDTO comment) {
        if (comment.getParentId() != null) {
            return commentService.getCommentById(comment.getParentId()).orElse(null);
        }
        return null;
    }
}