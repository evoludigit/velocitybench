package com.velocitybench.healthcheck;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Health check probe types (Kubernetes-compatible).
 */
public enum ProbeType {
    LIVENESS("liveness"),
    READINESS("readiness"),
    STARTUP("startup");

    private final String value;

    ProbeType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static ProbeType fromString(String value) {
        for (ProbeType type : ProbeType.values()) {
            if (type.value.equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown probe type: " + value);
    }
}
