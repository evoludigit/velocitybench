package com.velocitybench.healthcheck;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Health check status values.
 */
public enum HealthStatus {
    UP("up"),
    DEGRADED("degraded"),
    DOWN("down"),
    IN_PROGRESS("in_progress");

    private final String value;

    HealthStatus(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static HealthStatus fromString(String value) {
        for (HealthStatus status : HealthStatus.values()) {
            if (status.value.equalsIgnoreCase(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown health status: " + value);
    }
}
