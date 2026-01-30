package com.velocitybench.model;

import java.time.LocalDateTime;
import java.util.UUID;

public class Comment {
    private int pkComment;
    private UUID id;
    private int fkPost;
    private int fkAuthor;
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Comment() {}

    public Comment(int pkComment, UUID id, int fkPost, int fkAuthor, String content,
                   LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.pkComment = pkComment;
        this.id = id;
        this.fkPost = fkPost;
        this.fkAuthor = fkAuthor;
        this.content = content;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public int getPkComment() { return pkComment; }
    public void setPkComment(int pkComment) { this.pkComment = pkComment; }
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    public int getFkPost() { return fkPost; }
    public void setFkPost(int fkPost) { this.fkPost = fkPost; }
    public int getFkAuthor() { return fkAuthor; }
    public void setFkAuthor(int fkAuthor) { this.fkAuthor = fkAuthor; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
