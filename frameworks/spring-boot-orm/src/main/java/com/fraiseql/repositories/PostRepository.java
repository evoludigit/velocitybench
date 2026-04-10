package com.fraiseql.repositories;

import com.fraiseql.entities.Post;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PostRepository extends JpaRepository<Post, Integer> {

    @Query(value = "SELECT * FROM benchmark.tb_post WHERE id = CAST(:id AS uuid)", nativeQuery = true)
    Post findByUuid(@Param("id") String id);

    @Query(value = "SELECT * FROM benchmark.tb_post WHERE published = true ORDER BY created_at DESC LIMIT :limit", nativeQuery = true)
    List<Post> findPublishedPostsWithLimit(@Param("limit") int limit);

    @Query(value = "SELECT p.id, p.title, p.content, p.created_at, u.username, u.full_name " +
                   "FROM posts p " +
                   "JOIN users u ON p.fk_author = u.pk_user " +
                   "WHERE p.published = true " +
                   "ORDER BY p.created_at DESC " +
                   "LIMIT ?1", nativeQuery = true)
    List<Object[]> findPublishedPostsWithAuthorLimit(int limit);

    List<Post> findByFkAuthor(Integer fkAuthor);

    @Query(value = "SELECT CAST(p.id AS text), p.title, p.content, p.created_at, CAST(u.id AS text) AS author_id, u.username, u.full_name " +
                   "FROM benchmark.tb_post p " +
                   "JOIN benchmark.tb_user u ON u.pk_user = p.fk_author " +
                   "WHERE p.published = true " +
                   "ORDER BY p.created_at DESC LIMIT :limit", nativeQuery = true)
    List<Object[]> findPublishedPostsWithAuthorJoin(@Param("limit") int limit);
}