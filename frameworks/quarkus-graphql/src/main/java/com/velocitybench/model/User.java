package com.velocitybench.model;

import java.time.LocalDateTime;
import java.util.UUID;

public class User {
    private int pkUser;
    private UUID id;
    private String username;
    private String fullName;
    private String bio;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public User() {}

    public User(int pkUser, UUID id, String username, String fullName, String bio,
                LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.pkUser = pkUser;
        this.id = id;
        this.username = username;
        this.fullName = fullName;
        this.bio = bio;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public int getPkUser() { return pkUser; }
    public void setPkUser(int pkUser) { this.pkUser = pkUser; }
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }
    public String getBio() { return bio; }
    public void setBio(String bio) { this.bio = bio; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
