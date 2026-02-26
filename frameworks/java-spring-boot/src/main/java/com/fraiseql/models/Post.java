package com.fraiseql.models;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;

@Entity
@Table(name = "tb_post", schema = "benchmark")
public class Post {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "pk_post")
    private Integer pkPost;

    @Column(name = "id", columnDefinition = "uuid")
    private String id;

    @Column(name = "identifier")
    private String identifier;

    @Column(name = "fk_author", nullable = false)
    private Integer fkAuthor;

    @Transient
    private String authorId;

    @Transient
    private com.fraiseql.models.User author;

    @NotBlank
    @Size(max = 500)
    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(name = "published")
    private Boolean published;

    @Column(name = "created_at", nullable = false)
    private java.time.LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private java.time.LocalDateTime updatedAt;

    // Getters and setters
    public Integer getPkPost() { return pkPost; }
    public void setPkPost(Integer pkPost) { this.pkPost = pkPost; }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getIdentifier() { return identifier; }
    public void setIdentifier(String identifier) { this.identifier = identifier; }

    public Integer getFkAuthor() { return fkAuthor; }
    public void setFkAuthor(Integer fkAuthor) { this.fkAuthor = fkAuthor; }

    public String getAuthorId() { return authorId; }
    public void setAuthorId(String authorId) { this.authorId = authorId; }

    public com.fraiseql.models.User getAuthor() { return author; }
    public void setAuthor(com.fraiseql.models.User author) { this.author = author; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Boolean getPublished() { return published; }
    public void setPublished(Boolean published) { this.published = published; }

    public java.time.LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.time.LocalDateTime createdAt) { this.createdAt = createdAt; }

    public java.time.LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(java.time.LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
