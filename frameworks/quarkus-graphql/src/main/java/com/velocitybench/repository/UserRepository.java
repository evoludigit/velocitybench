package com.velocitybench.repository;

import com.velocitybench.model.User;
import io.agroal.api.AgroalDataSource;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.sql.*;
import java.util.*;

@ApplicationScoped
public class UserRepository {

    @Inject
    AgroalDataSource dataSource;

    public Optional<User> findById(String id) {
        String sql = "SELECT pk_user, id, username, full_name, bio, created_at, updated_at FROM tb_user WHERE id = ?";
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

    public Map<Integer, User> findByPks(Set<Integer> pks) {
        if (pks.isEmpty()) return Collections.emptyMap();

        String placeholders = String.join(",", Collections.nCopies(pks.size(), "?"));
        String sql = "SELECT pk_user, id, username, full_name, bio, created_at, updated_at FROM tb_user WHERE pk_user IN (" + placeholders + ")";

        Map<Integer, User> result = new HashMap<>();
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            int i = 1;
            for (Integer pk : pks) {
                stmt.setInt(i++, pk);
            }
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    User user = mapRow(rs);
                    result.put(user.getPkUser(), user);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    public List<User> findAll(int limit) {
        String sql = "SELECT pk_user, id, username, full_name, bio, created_at, updated_at FROM tb_user ORDER BY pk_user LIMIT ?";
        List<User> users = new ArrayList<>();
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setInt(1, Math.min(limit, 100));
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    users.add(mapRow(rs));
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return users;
    }

    public Optional<User> update(String id, String fullName, String bio) {
        StringBuilder sql = new StringBuilder("UPDATE tb_user SET updated_at = NOW()");
        List<Object> params = new ArrayList<>();

        if (fullName != null) {
            sql.append(", full_name = ?");
            params.add(fullName);
        }
        if (bio != null) {
            sql.append(", bio = ?");
            params.add(bio);
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

    private User mapRow(ResultSet rs) throws SQLException {
        return new User(
            rs.getInt("pk_user"),
            rs.getString("id"),
            rs.getString("username"),
            rs.getString("full_name"),
            rs.getString("bio"),
            rs.getTimestamp("created_at").toLocalDateTime(),
            rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toLocalDateTime() : null
        );
    }
}
