package com.velocitybench.model;

import java.time.LocalDateTime;
import java.util.UUID;

public record User(
    int pkUser,
    UUID id,
    String username,
    String fullName,
    String bio,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
