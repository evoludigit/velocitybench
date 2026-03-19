package com.fraiseql.rest;

import com.fraiseql.dto.PostDTO;
import com.fraiseql.dto.PostWithAuthorDTO;
import com.fraiseql.service.PostService;
import com.fraiseql.metrics.ApplicationMetrics;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/posts")
public class PostController {

    private final PostService postService;
    private final ApplicationMetrics metrics;

    public PostController(PostService postService, ApplicationMetrics metrics) {
        this.postService = postService;
        this.metrics = metrics;
    }

    @GetMapping("/{id}")
    public ResponseEntity<PostDTO> getPost(@PathVariable String id) {
        metrics.incrementRestRequests();
        return postService.getPostById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<List<PostDTO>> listPosts(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {
        metrics.incrementRestRequests();
        List<PostDTO> posts = postService.getAllPosts(page, size);
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/with-author")
    public ResponseEntity<List<PostWithAuthorDTO>> listPostsWithAuthor(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {
        metrics.incrementRestRequests();
        return ResponseEntity.ok(postService.getPostsWithAuthor(page, size));
    }

    @GetMapping("/by-author/{authorId}")
    public ResponseEntity<List<PostDTO>> getPostsByAuthor(
        @PathVariable String authorId,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {
        metrics.incrementRestRequests();
        List<PostDTO> posts = postService.getPostsByAuthor(authorId, page, size);
        return ResponseEntity.ok(posts);
    }
}