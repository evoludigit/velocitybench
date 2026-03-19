package com.fraiseql.service;

import com.fraiseql.dto.PostDTO;
import com.fraiseql.dto.PostWithAuthorDTO;
import com.fraiseql.dto.UserDTO;
import com.fraiseql.models.Post;
import com.fraiseql.models.User;
import com.fraiseql.repository.PostRepository;
import com.fraiseql.repository.UserRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class PostService {

    private final PostRepository postRepository;
    private final UserRepository userRepository;

    public PostService(PostRepository postRepository, UserRepository userRepository) {
        this.postRepository = postRepository;
        this.userRepository = userRepository;
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

    public List<PostWithAuthorDTO> getPostsWithAuthor(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        List<Post> posts = postRepository.findByPublishedOrderByCreatedAtDesc(true, pageable);

        List<Integer> authorIds = posts.stream()
                .map(Post::getFkAuthor)
                .filter(Objects::nonNull)
                .distinct()
                .collect(Collectors.toList());

        Map<Integer, UserDTO> userMap = userRepository.findAllByPkUserIn(authorIds).stream()
                .collect(Collectors.toMap(User::getPkUser, this::toUserDTO));

        return posts.stream()
                .map(post -> toPostWithAuthorDTO(post, userMap))
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

    private PostWithAuthorDTO toPostWithAuthorDTO(Post post, Map<Integer, UserDTO> userMap) {
        PostWithAuthorDTO dto = new PostWithAuthorDTO();
        dto.setId(post.getId());
        dto.setTitle(post.getTitle());
        dto.setContent(post.getContent());
        dto.setCreatedAt(post.getCreatedAt() != null ? post.getCreatedAt().toString() : null);
        dto.setAuthor(userMap.get(post.getFkAuthor()));
        return dto;
    }

    private UserDTO toUserDTO(User user) {
        UserDTO dto = new UserDTO();
        dto.setId(user.getId());
        dto.setUsername(user.getUsername());
        dto.setFullName(user.getFullName());
        dto.setBio(user.getBio());
        return dto;
    }
}
