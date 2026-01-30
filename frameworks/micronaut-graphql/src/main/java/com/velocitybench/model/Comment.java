package com.velocitybench.model;

import java.time.LocalDateTime;
import java.util.UUID;

public record Comment(
    int pkComment,
    UUID id,
    int fkPost,
    int fkAuthor,
    String content,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
