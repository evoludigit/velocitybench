package com.fraiseql.rest;

import com.fraiseql.dto.UserDTO;
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
@RequestMapping("/api/users")
public class UserController {

    private final JdbcTemplate jdbcTemplate;

    public UserController(DataSource dataSource) {
        this.jdbcTemplate = new JdbcTemplate(dataSource);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUser(@PathVariable String id) {
        String sql = "SELECT u.id, u.username, u.full_name, u.bio " +
                    "FROM benchmark.tb_user u WHERE u.id = ?";

        List<UserDTO> users = jdbcTemplate.query(sql, new Object[]{id}, new UserRowMapper());

        if (!users.isEmpty()) {
            return ResponseEntity.ok(users.get(0));
        }
        return ResponseEntity.notFound().build();
    }

    @GetMapping
    public ResponseEntity<List<UserDTO>> listUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {

        String sql = "SELECT u.id, u.username, u.full_name, u.bio " +
                    "FROM benchmark.tb_user u " +
                    "ORDER BY u.created_at DESC LIMIT ?";

        List<UserDTO> users = jdbcTemplate.query(sql, new Object[]{size}, new UserRowMapper());
        return ResponseEntity.ok(users);
    }

    private static class UserRowMapper implements RowMapper<UserDTO> {
        @Override
        public UserDTO mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new UserDTO(
                rs.getString("id"),
                rs.getString("username"),
                rs.getString("full_name"),
                rs.getString("bio")
            );
        }
    }
}