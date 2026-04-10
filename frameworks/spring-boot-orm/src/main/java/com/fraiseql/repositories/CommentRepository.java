package com.fraiseql.repositories;

import com.fraiseql.entities.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Integer> {

    @Query(value = "SELECT c.pk_comment, c.id, c.fk_post, c.fk_author, c.content, c.created_at, c.updated_at " +
                   "FROM benchmark.tb_comment c " +
                   "JOIN benchmark.tb_post p ON p.pk_post = c.fk_post " +
                   "WHERE p.id = CAST(:postId AS uuid) " +
                   "ORDER BY c.created_at DESC LIMIT :limit", nativeQuery = true)
    List<Comment> findByPostUuid(@Param("postId") String postId, @Param("limit") int limit);
}
