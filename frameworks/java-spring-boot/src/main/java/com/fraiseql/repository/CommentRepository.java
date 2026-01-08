package com.fraiseql.repository;

import com.fraiseql.models.Comment;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, String> {

    List<Comment> findByPostIdOrderByCreatedAt(String postId, Pageable pageable);

    List<Comment> findByAuthorIdOrderByCreatedAt(String authorId, Pageable pageable);

    @Query("SELECT c FROM Comment c LEFT JOIN FETCH c.author WHERE c.post.id = :postId ORDER BY c.createdAt")
    List<Comment> findByPostIdWithAuthor(@Param("postId") String postId, Pageable pageable);
}