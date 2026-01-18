package com.velocitybench.model;

import java.time.LocalDateTime;

public record Comment(
    int pkComment,
    String id,
    int fkPost,
    int fkAuthor,
    String content,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
