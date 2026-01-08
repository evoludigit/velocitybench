package com.fraiseql.repository;

import com.fraiseql.models.Post;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PostRepository extends JpaRepository<Post, String> {

    List<Post> findByAuthorIdAndStatusOrderByCreatedAtDesc(String authorId, String status, Pageable pageable);

    @Query("SELECT p FROM Post p LEFT JOIN FETCH p.author WHERE p.id = :id")
    Optional<Post> findByIdWithAuthor(@Param("id") String id);

    List<Post> findByStatusOrderByCreatedAtDesc(String status, Pageable pageable);
}