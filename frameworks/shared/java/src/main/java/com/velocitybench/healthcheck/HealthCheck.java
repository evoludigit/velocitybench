package com.velocitybench.healthcheck;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.HashMap;
import java.util.Map;

/**
 * Individual health check result.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class HealthCheck {
    private HealthStatus status;

    @JsonProperty("response_time_ms")
    private Double responseTimeMs;

    private String error;
    private String warning;
    private String info;

    private Map<String, Object> additionalData;

    public HealthCheck(HealthStatus status) {
        this.status = status;
        this.additionalData = new HashMap<>();
    }

    public HealthStatus getStatus() {
        return status;
    }

    public void setStatus(HealthStatus status) {
        this.status = status;
    }

    public Double getResponseTimeMs() {
        return responseTimeMs;
    }

    public HealthCheck withResponseTime(double ms) {
        this.responseTimeMs = ms;
        return this;
    }

    public String getError() {
        return error;
    }

    public HealthCheck withError(String error) {
        this.error = error;
        return this;
    }

    public String getWarning() {
        return warning;
    }

    public HealthCheck withWarning(String warning) {
        this.warning = warning;
        return this;
    }

    public String getInfo() {
        return info;
    }

    public HealthCheck withInfo(String info) {
        this.info = info;
        return this;
    }

    public Map<String, Object> getAdditionalData() {
        return additionalData;
    }

    public HealthCheck withData(String key, Object value) {
        this.additionalData.put(key, value);
        return this;
    }
}
