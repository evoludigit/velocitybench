package com.fraiseql.dto;

public class PostWithAuthorDTO {
    private String id;
    private String title;
    private String content;
    private UserDTO author;
    private String createdAt;

    public PostWithAuthorDTO() {}

    // Getters
    public String getId() { return id; }
    public String getTitle() { return title; }
    public String getContent() { return content; }
    public UserDTO getAuthor() { return author; }
    public String getCreatedAt() { return createdAt; }

    // Setters
    public void setId(String id) { this.id = id; }
    public void setTitle(String title) { this.title = title; }
    public void setContent(String content) { this.content = content; }
    public void setAuthor(UserDTO author) { this.author = author; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}
