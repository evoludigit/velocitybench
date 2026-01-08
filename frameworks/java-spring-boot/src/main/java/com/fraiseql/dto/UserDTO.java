package com.fraiseql.dto;

public class UserDTO {
    private String id;
    private String username;
    private String fullName;
    private String bio;

    public UserDTO() {}

    public UserDTO(String id, String username, String fullName, String bio) {
        this.id = id;
        this.username = username;
        this.fullName = fullName;
        this.bio = bio;
    }

    // Getters
    public String getId() { return id; }
    public String getUsername() { return username; }
    public String getFullName() { return fullName; }
    public String getBio() { return bio; }

    // Setters
    public void setId(String id) { this.id = id; }
    public void setUsername(String username) { this.username = username; }
    public void setFullName(String fullName) { this.fullName = fullName; }
    public void setBio(String bio) { this.bio = bio; }
}