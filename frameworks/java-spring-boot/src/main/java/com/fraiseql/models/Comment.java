package com.fraiseql.models;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.util.UUID;

@Entity
@Table(name = "tb_comment", schema = "benchmark")
public class Comment {

    @Id
    @Column(columnDefinition = "uuid")
    private UUID id;

    @Column(name = "post_id", nullable = false, columnDefinition = "uuid")
    private UUID postId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "post_id", insertable = false, updatable = false)
    private Post post;

    @Column(name = "author_id", nullable = false, columnDefinition = "uuid")
    private UUID authorId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "author_id", insertable = false, updatable = false)
    private User author;

    @Column(name = "parent_id", columnDefinition = "uuid")
    private UUID parentId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_id", insertable = false, updatable = false)
    private Comment parent;

    @NotBlank
    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    @Column(name = "is_approved", nullable = false)
    private Boolean isApproved = true;

    @Column(name = "created_at", nullable = false)
    private java.time.LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private java.time.LocalDateTime updatedAt;

    // Getters and setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getPostId() { return postId; }
    public void setPostId(UUID postId) { this.postId = postId; }

    public Post getPost() { return post; }
    public void setPost(Post post) { this.post = post; }

    public UUID getAuthorId() { return authorId; }
    public void setAuthorId(UUID authorId) { this.authorId = authorId; }

    public User getAuthor() { return author; }
    public void setAuthor(User author) { this.author = author; }

    public UUID getParentId() { return parentId; }
    public void setParentId(UUID parentId) { this.parentId = parentId; }

    public Comment getParent() { return parent; }
    public void setParent(Comment parent) { this.parent = parent; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Boolean getIsApproved() { return isApproved; }
    public void setIsApproved(Boolean isApproved) { this.isApproved = isApproved; }

    public java.time.LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.time.LocalDateTime createdAt) { this.createdAt = createdAt; }

    public java.time.LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(java.time.LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}