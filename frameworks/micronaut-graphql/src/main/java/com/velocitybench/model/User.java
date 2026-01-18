package com.velocitybench.model;

import java.time.LocalDateTime;

public record User(
    int pkUser,
    String id,
    String username,
    String fullName,
    String bio,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
