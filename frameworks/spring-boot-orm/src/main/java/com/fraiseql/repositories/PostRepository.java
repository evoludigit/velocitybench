package com.fraiseql.repositories;

import com.fraiseql.entities.Post;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PostRepository extends JpaRepository<Post, Integer> {

    Post findById(String uuid);

    @Query("SELECT p FROM Post p JOIN FETCH p.author WHERE p.published = true ORDER BY p.createdAt DESC")
    List<Post> findPublishedPostsWithAuthor(Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.published = true ORDER BY p.createdAt DESC")
    List<Post> findPublishedPostsWithLimit(int limit);

    @Query(value = "SELECT p.id, p.title, p.content, p.created_at, u.username, u.full_name " +
                   "FROM posts p " +
                   "JOIN users u ON p.fk_author = u.pk_user " +
                   "WHERE p.published = true " +
                   "ORDER BY p.created_at DESC " +
                   "LIMIT ?1", nativeQuery = true)
    List<Object[]> findPublishedPostsWithAuthorLimit(int limit);

    List<Post> findByFkAuthor(Integer fkAuthor);


}