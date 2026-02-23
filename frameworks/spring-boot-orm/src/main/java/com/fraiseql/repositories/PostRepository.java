package com.fraiseql.repositories;

import com.fraiseql.entities.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PostRepository extends JpaRepository<Post, Integer> {

    @Query(value = "SELECT * FROM benchmark.tb_post WHERE id = :id", nativeQuery = true)
    Post findByUuid(@Param("id") String id);

    @Query(value = "SELECT * FROM benchmark.tb_post WHERE published = true ORDER BY created_at DESC LIMIT :limit", nativeQuery = true)
    List<Post> findPublishedPostsWithLimit(@Param("limit") int limit);

    /**
     * Fetches published posts with joined author data.
     * Each row: [id(uuid), title, content, created_at, username, full_name]
     */
    @Query(value = "SELECT p.id, p.title, p.content, p.created_at, u.username, u.full_name " +
                   "FROM benchmark.tb_post p " +
                   "JOIN benchmark.tb_user u ON p.fk_author = u.pk_user " +
                   "WHERE p.published = true " +
                   "ORDER BY p.created_at DESC " +
                   "LIMIT :limit",
           nativeQuery = true)
    List<Object[]> findPublishedPostsWithAuthorLimit(@Param("limit") int limit);

    List<Post> findByFkAuthor(Integer fkAuthor);
}