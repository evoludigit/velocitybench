package com.fraiseql.service;

import com.fraiseql.dto.CommentDTO;
import com.fraiseql.models.Comment;
import com.fraiseql.repository.CommentRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class CommentService {

    private final CommentRepository commentRepository;

    public CommentService(CommentRepository commentRepository) {
        this.commentRepository = commentRepository;
    }

    public List<CommentDTO> getCommentsByPost(String postId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Integer fkPost = Integer.parseInt(postId);
        List<Comment> comments = commentRepository.findByFkPostOrderByCreatedAt(fkPost, pageable);
        return comments.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public List<CommentDTO> getCommentsByAuthor(String authorId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Integer fkAuthor = Integer.parseInt(authorId);
        List<Comment> comments = commentRepository.findByFkAuthorOrderByCreatedAt(fkAuthor, pageable);
        return comments.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public Optional<CommentDTO> getCommentById(String id) {
        try {
            Integer pkComment = Integer.parseInt(id);
            return commentRepository.findById(pkComment)
                    .map(this::toDTO);
        } catch (NumberFormatException e) {
            return Optional.empty();
        }
    }

    private CommentDTO toDTO(Comment comment) {
        if (comment == null) {
            return null;
        }
        CommentDTO dto = new CommentDTO();
        dto.setId(comment.getId());
        dto.setContent(comment.getContent());
        dto.setPostId(comment.getFkPost() != null ? comment.getFkPost().toString() : null);
        dto.setAuthorId(comment.getFkAuthor() != null ? comment.getFkAuthor().toString() : null);
        dto.setParentId(comment.getFkParent() != null ? comment.getFkParent().toString() : null);
        dto.setIsApproved(comment.getIsApproved());
        dto.setCreatedAt(comment.getCreatedAt() != null ? comment.getCreatedAt().toString() : null);
        return dto;
    }
}
