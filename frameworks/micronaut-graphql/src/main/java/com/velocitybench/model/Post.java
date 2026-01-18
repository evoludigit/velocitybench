package com.velocitybench.model;

import java.time.LocalDateTime;

public record Post(
    int pkPost,
    String id,
    int fkAuthor,
    String title,
    String content,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
