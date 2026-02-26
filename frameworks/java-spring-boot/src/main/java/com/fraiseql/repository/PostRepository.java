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
public interface PostRepository extends JpaRepository<Post, Integer> {

    List<Post> findByFkAuthorAndPublishedOrderByCreatedAtDesc(Integer fkAuthor, Boolean published, Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.id = :uuid")
    Optional<Post> findByUuid(@Param("uuid") String uuid);

    List<Post> findByPublishedOrderByCreatedAtDesc(Boolean published, Pageable pageable);
}
