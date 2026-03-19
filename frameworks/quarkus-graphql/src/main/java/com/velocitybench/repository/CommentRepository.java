package com.velocitybench.repository;

import com.velocitybench.model.Comment;
import io.agroal.api.AgroalDataSource;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.sql.*;
import java.util.*;

@ApplicationScoped
public class CommentRepository {

    @Inject
    AgroalDataSource dataSource;

    public List<Comment> findAll(int limit) {
        String sql = "SELECT pk_comment, id, fk_post, fk_author, content, created_at, updated_at " +
                     "FROM benchmark.tb_comment ORDER BY pk_comment LIMIT ?";
        List<Comment> result = new ArrayList<>();
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setInt(1, limit);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    result.add(mapRow(rs));
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    public Map<Integer, List<Comment>> findByPostPks(Set<Integer> postPks, int limit) {
        if (postPks.isEmpty()) return Collections.emptyMap();

        String placeholders = String.join(",", Collections.nCopies(postPks.size(), "?"));
        String sql = """
            SELECT * FROM (
                SELECT pk_comment, id, fk_post, fk_author, content, created_at, updated_at,
                       ROW_NUMBER() OVER (PARTITION BY fk_post ORDER BY pk_comment) as rn
                FROM tb_comment WHERE fk_post IN (%s)
            ) t WHERE rn <= ?
            ORDER BY fk_post, pk_comment
            """.formatted(placeholders);

        Map<Integer, List<Comment>> result = new HashMap<>();
        for (Integer pk : postPks) {
            result.put(pk, new ArrayList<>());
        }

        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            int i = 1;
            for (Integer pk : postPks) {
                stmt.setInt(i++, pk);
            }
            stmt.setInt(i, limit);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Comment comment = mapRow(rs);
                    result.get(comment.getFkPost()).add(comment);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    private Comment mapRow(ResultSet rs) throws SQLException {
        return new Comment(
            rs.getInt("pk_comment"),
            rs.getObject("id", UUID.class),
            rs.getInt("fk_post"),
            rs.getInt("fk_author"),
            rs.getString("content"),
            rs.getTimestamp("created_at").toLocalDateTime(),
            rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toLocalDateTime() : null
        );
    }
}
