package com.fraiseql.rest;

import com.fraiseql.dto.UserDTO;
import com.fraiseql.service.UserService;
import com.fraiseql.metrics.ApplicationMetrics;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;
    private final ApplicationMetrics metrics;

    public UserController(UserService userService, ApplicationMetrics metrics) {
        this.userService = userService;
        this.metrics = metrics;
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUser(@PathVariable String id) {
        metrics.incrementRestRequests();
        return userService.getUserById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<List<UserDTO>> listUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {
        metrics.incrementRestRequests();
        List<UserDTO> users = userService.getAllUsers(page, size);
        return ResponseEntity.ok(users);
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserDTO> updateUser(
        @PathVariable String id,
        @RequestBody Map<String, String> body) {
        metrics.incrementRestRequests();
        String bio = body.get("bio");
        return userService.updateBio(id, bio)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}