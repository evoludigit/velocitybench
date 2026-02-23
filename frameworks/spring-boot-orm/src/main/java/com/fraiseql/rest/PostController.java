package com.fraiseql.rest;

import com.fraiseql.dto.PostAuthorDTO;
import com.fraiseql.dto.PostDTO;
import com.fraiseql.dto.PostWithAuthorDTO;
import com.fraiseql.entities.Post;
import com.fraiseql.entities.User;
import com.fraiseql.repositories.PostRepository;
import com.fraiseql.repositories.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/posts")
public class PostController {

    private final PostRepository postRepository;
    private final UserRepository userRepository;

    public PostController(PostRepository postRepository, UserRepository userRepository) {
        this.postRepository = postRepository;
        this.userRepository = userRepository;
    }

    @GetMapping("/{id}")
    public ResponseEntity<PostDTO> getPost(@PathVariable String id) {
        Post post = postRepository.findByUuid(id);
        if (post != null) {
            PostDTO postDTO = new PostDTO(
                post.getId(),
                post.getTitle(),
                post.getContent(),
                post.getFkAuthor() != null ? String.valueOf(post.getFkAuthor()) : null,
                post.getCreatedAt()
            );
            return ResponseEntity.ok(postDTO);
        }
        return ResponseEntity.notFound().build();
    }

    @GetMapping
    public ResponseEntity<?> listPosts(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(required = false) String include) {

        if ("author".equals(include)) {
            List<Object[]> rows = postRepository.findPublishedPostsWithAuthorLimit(size);
            List<PostWithAuthorDTO> result = rows.stream()
                .map(row -> new PostWithAuthorDTO(
                    (String) row[0],
                    (String) row[1],
                    (String) row[2],
                    row[3] instanceof Timestamp ? ((Timestamp) row[3]).toLocalDateTime() : (LocalDateTime) row[3],
                    new PostAuthorDTO((String) row[4], (String) row[5])
                ))
                .collect(Collectors.toList());
            return ResponseEntity.ok(result);
        }

        List<Post> posts = postRepository.findPublishedPostsWithLimit(size);
        List<PostDTO> postDTOs = posts.stream()
            .map(post -> new PostDTO(
                post.getId(),
                post.getTitle(),
                post.getContent(),
                post.getFkAuthor() != null ? String.valueOf(post.getFkAuthor()) : null,
                post.getCreatedAt()
            ))
            .collect(Collectors.toList());
        return ResponseEntity.ok(postDTOs);
    }

    @GetMapping("/with-author")
    public ResponseEntity<List<PostWithAuthorDTO>> listPostsWithAuthor(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {

        List<Object[]> rows = postRepository.findPublishedPostsWithAuthorLimit(size);
        List<PostWithAuthorDTO> result = rows.stream()
            .map(row -> new PostWithAuthorDTO(
                (String) row[0],
                (String) row[1],
                (String) row[2],
                row[3] instanceof Timestamp ? ((Timestamp) row[3]).toLocalDateTime() : (LocalDateTime) row[3],
                new PostAuthorDTO((String) row[4], (String) row[5])
            ))
            .collect(Collectors.toList());
        return ResponseEntity.ok(result);
    }

    @GetMapping("/by-author/{authorId}")
    public ResponseEntity<List<PostDTO>> getPostsByAuthor(
        @PathVariable String authorId,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {

        User user = userRepository.findByUuid(authorId);
        if (user == null) {
            return ResponseEntity.ok(Collections.emptyList());
        }

        List<Post> posts = postRepository.findByFkAuthor(user.getPkUser());
        List<PostDTO> postDTOs = posts.stream()
            .map(post -> new PostDTO(
                post.getId(),
                post.getTitle(),
                post.getContent(),
                post.getFkAuthor() != null ? String.valueOf(post.getFkAuthor()) : null,
                post.getCreatedAt()
            ))
            .collect(Collectors.toList());
        return ResponseEntity.ok(postDTOs);
    }
}