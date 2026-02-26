package com.velocitybench.model;

import java.time.LocalDateTime;
import java.util.UUID;

public record Post(
    int pkPost,
    UUID id,
    int fkAuthor,
    String title,
    String content,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
