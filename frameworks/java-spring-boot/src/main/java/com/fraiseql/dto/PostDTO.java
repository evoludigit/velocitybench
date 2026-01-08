package com.fraiseql.dto;

public class PostDTO {
    private String id;
    private String title;
    private String content;
    private String authorId;
    private String createdAt;

    public PostDTO() {}

    public PostDTO(String id, String title, String content, String authorId, String createdAt) {
        this.id = id;
        this.title = title;
        this.content = content;
        this.authorId = authorId;
        this.createdAt = createdAt;
    }

    // Getters
    public String getId() { return id; }
    public String getTitle() { return title; }
    public String getContent() { return content; }
    public String getAuthorId() { return authorId; }
    public String getCreatedAt() { return createdAt; }

    // Setters
    public void setId(String id) { this.id = id; }
    public void setTitle(String title) { this.title = title; }
    public void setContent(String content) { this.content = content; }
    public void setAuthorId(String authorId) { this.authorId = authorId; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}