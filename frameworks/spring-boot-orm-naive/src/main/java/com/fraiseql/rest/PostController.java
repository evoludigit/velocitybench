package com.fraiseql.rest;

import com.fraiseql.dto.CommentDTO;
import com.fraiseql.dto.PostAuthorDTO;
import com.fraiseql.dto.PostDTO;
import com.fraiseql.dto.PostWithAuthorDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import javax.sql.DataSource;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/posts")
public class PostController {

    private final JdbcTemplate jdbcTemplate;

    public PostController(DataSource dataSource) {
        this.jdbcTemplate = new JdbcTemplate(dataSource);
    }

    @GetMapping("/{id}")
    public ResponseEntity<PostDTO> getPost(@PathVariable String id) {
        String sql = "SELECT p.id, p.title, p.content, p.fk_author, p.created_at " +
                    "FROM benchmark.tb_post p WHERE p.id = CAST(? AS uuid) AND p.published = true";

        List<PostDTO> posts = jdbcTemplate.query(sql, new Object[]{id}, new PostRowMapper());

        if (!posts.isEmpty()) {
            return ResponseEntity.ok(posts.get(0));
        }
        return ResponseEntity.notFound().build();
    }

    @GetMapping
    public ResponseEntity<?> listPosts(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(required = false) String include) {

        if ("author".equals(include)) {
            // Q2b: naive N+1 — one query per post to fetch its author (intentional for comparison)
            String postSql = "SELECT p.id, p.title, p.content, p.fk_author, p.created_at " +
                        "FROM benchmark.tb_post p " +
                        "WHERE p.published = true " +
                        "ORDER BY p.created_at DESC LIMIT ?";
            List<PostDTO> posts = jdbcTemplate.query(postSql, new Object[]{size}, new PostRowMapper());

            String authorSql = "SELECT CAST(u.id AS text), u.username, u.full_name " +
                        "FROM benchmark.tb_user u WHERE u.pk_user = ?";
            List<PostWithAuthorDTO> result = new ArrayList<>(posts.size());
            for (PostDTO post : posts) {
                int fkAuthor = post.getAuthorId() != null ? Integer.parseInt(post.getAuthorId()) : 0;
                List<PostAuthorDTO> authors = jdbcTemplate.query(authorSql, new Object[]{fkAuthor},
                    (rs, rowNum) -> new PostAuthorDTO(
                        rs.getString(1),
                        rs.getString("username"),
                        rs.getString("full_name")
                    ));
                PostAuthorDTO author = authors.isEmpty() ? new PostAuthorDTO("", "", "") : authors.get(0);
                result.add(new PostWithAuthorDTO(post.getId(), post.getTitle(), post.getContent(), post.getCreatedAt(), author));
            }
            return ResponseEntity.ok(result);
        }

        String sql = "SELECT p.id, p.title, p.content, p.fk_author, p.created_at " +
                    "FROM benchmark.tb_post p " +
                    "WHERE p.published = true " +
                    "ORDER BY p.created_at DESC LIMIT ?";

        List<PostDTO> posts = jdbcTemplate.query(sql, new Object[]{size}, new PostRowMapper());
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/by-author/{authorId}")
    public ResponseEntity<List<PostDTO>> getPostsByAuthor(
        @PathVariable String authorId,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {

        String sql = "SELECT p.id, p.title, p.content, p.fk_author, p.created_at " +
                    "FROM benchmark.tb_post p " +
                    "JOIN benchmark.tb_user u ON p.fk_author = u.pk_user " +
                    "WHERE u.id = CAST(? AS uuid) AND p.published = true " +
                    "ORDER BY p.created_at DESC LIMIT ?";

        List<PostDTO> posts = jdbcTemplate.query(sql, new Object[]{authorId, size}, new PostRowMapper());
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/{postId}/comments")
    public ResponseEntity<List<CommentDTO>> getCommentsByPost(
        @PathVariable String postId,
        @RequestParam(defaultValue = "10") int limit) {

        // Naive: individual lookups per comment (intentional N+1 for benchmark comparison)
        String sql = "SELECT c.id, c.content, c.fk_author, c.created_at " +
                    "FROM benchmark.tb_comment c " +
                    "JOIN benchmark.tb_post p ON p.pk_post = c.fk_post " +
                    "WHERE p.id = CAST(? AS uuid) " +
                    "ORDER BY c.created_at DESC LIMIT ?";

        List<CommentDTO> comments = jdbcTemplate.query(sql, new Object[]{postId, limit}, (rs, rowNum) ->
            new CommentDTO(
                rs.getString("id"),
                rs.getString("content"),
                postId,
                String.valueOf(rs.getInt("fk_author")),
                rs.getTimestamp("created_at").toLocalDateTime()
            )
        );
        return ResponseEntity.ok(comments);
    }

    private static class PostRowMapper implements RowMapper<PostDTO> {
        @Override
        public PostDTO mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new PostDTO(
                rs.getString("id"),
                rs.getString("title"),
                rs.getString("content"),
                rs.getInt("fk_author") != 0 ? String.valueOf(rs.getInt("fk_author")) : null,
                rs.getTimestamp("created_at").toLocalDateTime()
            );
        }
    }
}