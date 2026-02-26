package com.fraiseql.models;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;

@Entity
@Table(name = "tb_comment", schema = "benchmark")
public class Comment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "pk_comment")
    private Integer pkComment;

    @Column(name = "id", columnDefinition = "uuid")
    private String id;

    @Column(name = "identifier")
    private String identifier;

    @Column(name = "fk_post", nullable = false)
    private Integer fkPost;

    @Column(name = "fk_author", nullable = false)
    private Integer fkAuthor;

    @Column(name = "fk_parent")
    private Integer fkParent;

    @NotBlank
    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    @Column(name = "is_approved", nullable = false)
    private Boolean isApproved = true;

    @Column(name = "created_at", nullable = false)
    private java.time.LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private java.time.LocalDateTime updatedAt;

    @Transient
    private User author;

    @Transient
    private Post post;

    // Getters and setters
    public Integer getPkComment() { return pkComment; }
    public void setPkComment(Integer pkComment) { this.pkComment = pkComment; }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getIdentifier() { return identifier; }
    public void setIdentifier(String identifier) { this.identifier = identifier; }

    public Integer getFkPost() { return fkPost; }
    public void setFkPost(Integer fkPost) { this.fkPost = fkPost; }

    public Integer getFkAuthor() { return fkAuthor; }
    public void setFkAuthor(Integer fkAuthor) { this.fkAuthor = fkAuthor; }

    public Integer getFkParent() { return fkParent; }
    public void setFkParent(Integer fkParent) { this.fkParent = fkParent; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Boolean getIsApproved() { return isApproved; }
    public void setIsApproved(Boolean isApproved) { this.isApproved = isApproved; }

    public java.time.LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.time.LocalDateTime createdAt) { this.createdAt = createdAt; }

    public java.time.LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(java.time.LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    public User getAuthor() { return author; }
    public void setAuthor(User author) { this.author = author; }

    public Post getPost() { return post; }
    public void setPost(Post post) { this.post = post; }
}
