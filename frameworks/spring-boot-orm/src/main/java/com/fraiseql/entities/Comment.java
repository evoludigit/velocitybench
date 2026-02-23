package com.fraiseql.entities;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "tb_comment", schema = "benchmark")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Comment {

    @Id
    @Column(name = "pk_comment")
    private Integer pkComment;

    @Column(name = "id", columnDefinition = "uuid")
    private String id;

    @Column(name = "fk_post")
    private Integer fkPost;

    @Column(name = "fk_author")
    private Integer fkAuthor;

    @Column(name = "content")
    private String content;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}