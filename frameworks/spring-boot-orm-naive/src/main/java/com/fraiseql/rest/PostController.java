package com.fraiseql.rest;

import com.fraiseql.dto.PostDTO;
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
                    "FROM benchmark.tb_post p WHERE p.id = ? AND p.published = true";

        List<PostDTO> posts = jdbcTemplate.query(sql, new Object[]{id}, new PostRowMapper());

        if (!posts.isEmpty()) {
            return ResponseEntity.ok(posts.get(0));
        }
        return ResponseEntity.notFound().build();
    }

    @GetMapping
    public ResponseEntity<List<PostDTO>> listPosts(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {

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
                    "WHERE u.id = ? AND p.published = true " +
                    "ORDER BY p.created_at DESC LIMIT ?";

        List<PostDTO> posts = jdbcTemplate.query(sql, new Object[]{authorId, size}, new PostRowMapper());
        return ResponseEntity.ok(posts);
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