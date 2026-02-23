package com.velocitybench.repository;

import com.velocitybench.model.Comment;
import jakarta.inject.Singleton;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

@Singleton
public class CommentRepository {

    private final DataSource dataSource;

    public CommentRepository(DataSource dataSource) {
        this.dataSource = dataSource;
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
                    result.get(comment.fkPost()).add(comment);
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
            rs.getObject("id", java.util.UUID.class),
            rs.getInt("fk_post"),
            rs.getInt("fk_author"),
            rs.getString("content"),
            rs.getTimestamp("created_at").toLocalDateTime(),
            rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toLocalDateTime() : null
        );
    }
}
