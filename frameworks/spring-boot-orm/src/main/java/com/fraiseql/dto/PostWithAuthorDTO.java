package com.fraiseql.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PostWithAuthorDTO {
    private String id;
    private String title;
    private String content;
    private LocalDateTime createdAt;
    private PostAuthorDTO author;
}
