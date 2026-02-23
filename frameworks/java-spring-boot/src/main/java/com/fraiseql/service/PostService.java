package com.fraiseql.service;

import com.fraiseql.dto.PostDTO;
import com.fraiseql.models.Post;
import com.fraiseql.repository.PostRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class PostService {

    private final PostRepository postRepository;

    public PostService(PostRepository postRepository) {
        this.postRepository = postRepository;
    }

    public Optional<PostDTO> getPostById(String id) {
        return postRepository.findByUuid(id)
                .map(this::toDTO);
    }

    public List<PostDTO> getAllPosts(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        List<Post> posts = postRepository.findByPublishedOrderByCreatedAtDesc(true, pageable);
        return posts.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public List<PostDTO> getPostsByAuthor(String authorId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Integer fkAuthor = Integer.parseInt(authorId);
        List<Post> posts = postRepository.findByFkAuthorAndPublishedOrderByCreatedAtDesc(fkAuthor, true, pageable);
        return posts.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    private PostDTO toDTO(Post post) {
        if (post == null) {
            return null;
        }
        PostDTO dto = new PostDTO();
        dto.setId(post.getId());
        dto.setTitle(post.getTitle());
        dto.setContent(post.getContent());
        dto.setAuthorId(post.getFkAuthor() != null ? post.getFkAuthor().toString() : null);
        dto.setCreatedAt(post.getCreatedAt() != null ? post.getCreatedAt().toString() : null);
        return dto;
    }
}
