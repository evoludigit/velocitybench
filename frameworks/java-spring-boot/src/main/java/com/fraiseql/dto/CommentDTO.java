package com.fraiseql.dto;

public class CommentDTO {
    private String id;
    private String content;
    private String postId;
    private String authorId;
    private String parentId;
    private Boolean isApproved;
    private String createdAt;

    public CommentDTO() {}

    public CommentDTO(String id, String content, String postId, String authorId, String parentId, Boolean isApproved, String createdAt) {
        this.id = id;
        this.content = content;
        this.postId = postId;
        this.authorId = authorId;
        this.parentId = parentId;
        this.isApproved = isApproved;
        this.createdAt = createdAt;
    }

    // Getters
    public String getId() { return id; }
    public String getContent() { return content; }
    public String getPostId() { return postId; }
    public String getAuthorId() { return authorId; }
    public String getParentId() { return parentId; }
    public Boolean getIsApproved() { return isApproved; }
    public String getCreatedAt() { return createdAt; }

    // Setters
    public void setId(String id) { this.id = id; }
    public void setContent(String content) { this.content = content; }
    public void setPostId(String postId) { this.postId = postId; }
    public void setAuthorId(String authorId) { this.authorId = authorId; }
    public void setParentId(String parentId) { this.parentId = parentId; }
    public void setIsApproved(Boolean isApproved) { this.isApproved = isApproved; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}