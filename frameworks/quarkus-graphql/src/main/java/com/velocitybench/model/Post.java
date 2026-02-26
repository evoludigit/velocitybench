package com.velocitybench.model;

import java.time.LocalDateTime;
import java.util.UUID;

public class Post {
    private int pkPost;
    private UUID id;
    private int fkAuthor;
    private String title;
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Post() {}

    public Post(int pkPost, UUID id, int fkAuthor, String title, String content,
                LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.pkPost = pkPost;
        this.id = id;
        this.fkAuthor = fkAuthor;
        this.title = title;
        this.content = content;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public int getPkPost() { return pkPost; }
    public void setPkPost(int pkPost) { this.pkPost = pkPost; }
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    public int getFkAuthor() { return fkAuthor; }
    public void setFkAuthor(int fkAuthor) { this.fkAuthor = fkAuthor; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
