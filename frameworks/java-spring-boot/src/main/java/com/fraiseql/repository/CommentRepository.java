package com.fraiseql.repository;

import com.fraiseql.models.Comment;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Integer> {

    List<Comment> findByFkPostOrderByCreatedAt(Integer fkPost, Pageable pageable);

    List<Comment> findByFkAuthorOrderByCreatedAt(Integer fkAuthor, Pageable pageable);
}
