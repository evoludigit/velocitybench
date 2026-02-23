package com.velocitybench.repository;

import com.velocitybench.model.Post;
import io.agroal.api.AgroalDataSource;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.sql.*;
import java.util.*;

@ApplicationScoped
public class PostRepository {

    @Inject
    AgroalDataSource dataSource;

    public Optional<Post> findById(String id) {
        String sql = "SELECT pk_post, id, fk_author, title, content, created_at, updated_at FROM tb_post WHERE id = ?";
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setObject(1, UUID.fromString(id));
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return Optional.of(mapRow(rs));
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Optional.empty();
    }

    public Map<Integer, Post> findByPks(Set<Integer> pks) {
        if (pks.isEmpty()) return Collections.emptyMap();

        String placeholders = String.join(",", Collections.nCopies(pks.size(), "?"));
        String sql = "SELECT pk_post, id, fk_author, title, content, created_at, updated_at FROM tb_post WHERE pk_post IN (" + placeholders + ")";

        Map<Integer, Post> result = new HashMap<>();
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            int i = 1;
            for (Integer pk : pks) {
                stmt.setInt(i++, pk);
            }
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Post post = mapRow(rs);
                    result.put(post.getPkPost(), post);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    public Map<Integer, List<Post>> findByAuthorPks(Set<Integer> authorPks, int limit) {
        if (authorPks.isEmpty()) return Collections.emptyMap();

        String placeholders = String.join(",", Collections.nCopies(authorPks.size(), "?"));
        String sql = """
            SELECT * FROM (
                SELECT pk_post, id, fk_author, title, content, created_at, updated_at,
                       ROW_NUMBER() OVER (PARTITION BY fk_author ORDER BY pk_post) as rn
                FROM tb_post WHERE fk_author IN (%s)
            ) t WHERE rn <= ?
            ORDER BY fk_author, pk_post
            """.formatted(placeholders);

        Map<Integer, List<Post>> result = new HashMap<>();
        for (Integer pk : authorPks) {
            result.put(pk, new ArrayList<>());
        }

        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            int i = 1;
            for (Integer pk : authorPks) {
                stmt.setInt(i++, pk);
            }
            stmt.setInt(i, limit);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Post post = mapRow(rs);
                    result.get(post.getFkAuthor()).add(post);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    public List<Post> findAll(int limit) {
        String sql = "SELECT pk_post, id, fk_author, title, content, created_at, updated_at FROM tb_post ORDER BY pk_post LIMIT ?";
        List<Post> posts = new ArrayList<>();
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setInt(1, Math.min(limit, 100));
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    posts.add(mapRow(rs));
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return posts;
    }

    public Optional<Post> update(String id, String title, String content) {
        StringBuilder sql = new StringBuilder("UPDATE tb_post SET updated_at = NOW()");
        List<Object> params = new ArrayList<>();

        if (title != null) {
            sql.append(", title = ?");
            params.add(title);
        }
        if (content != null) {
            sql.append(", content = ?");
            params.add(content);
        }

        sql.append(" WHERE id = ?");
        params.add(UUID.fromString(id));

        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql.toString())) {
            for (int i = 0; i < params.size(); i++) {
                stmt.setObject(i + 1, params.get(i));
            }
            stmt.executeUpdate();
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }

        return findById(id);
    }

    private Post mapRow(ResultSet rs) throws SQLException {
        return new Post(
            rs.getInt("pk_post"),
            rs.getObject("id", UUID.class),
            rs.getInt("fk_author"),
            rs.getString("title"),
            rs.getString("content"),
            rs.getTimestamp("created_at").toLocalDateTime(),
            rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toLocalDateTime() : null
        );
    }
}
