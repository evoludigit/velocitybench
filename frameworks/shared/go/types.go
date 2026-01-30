// Package healthcheck provides standardized health check functionality for VelocityBench Go frameworks.
//
// Implements Kubernetes-compatible health probes (liveness, readiness, startup)
// with database connectivity checks and memory monitoring.
package healthcheck

import (
	"time"
)

// HealthStatus represents the health status of a service or check.
type HealthStatus string

const (
	// StatusUp indicates the service or check is healthy.
	StatusUp HealthStatus = "up"
	// StatusDegraded indicates the service is functional but with warnings.
	StatusDegraded HealthStatus = "degraded"
	// StatusDown indicates the service or check is unhealthy.
	StatusDown HealthStatus = "down"
	// StatusInProgress indicates initialization is in progress (startup probe).
	StatusInProgress HealthStatus = "in_progress"
)

// ProbeType represents the type of health check probe.
type ProbeType string

const (
	// ProbeLiveness checks if the process is alive.
	ProbeLiveness ProbeType = "liveness"
	// ProbeReadiness checks if the service can handle traffic.
	ProbeReadiness ProbeType = "readiness"
	// ProbeStartup checks if initialization is complete.
	ProbeStartup ProbeType = "startup"
)

// HealthCheck represents an individual health check result.
type HealthCheck struct {
	Status         HealthStatus           `json:"status"`
	ResponseTimeMs *float64               `json:"response_time_ms,omitempty"`
	Error          *string                `json:"error,omitempty"`
	Warning        *string                `json:"warning,omitempty"`
	Info           *string                `json:"info,omitempty"`
	AdditionalData map[string]interface{} `json:"-"` // Embedded in JSON via MarshalJSON
}

// MarshalJSON implements custom JSON marshaling to include additional data.
func (hc HealthCheck) MarshalJSON() ([]byte, error) {
	type Alias HealthCheck
	aux := struct {
		Alias
	}{
		Alias: (Alias)(hc),
	}

	// Merge additional data
	m := make(map[string]interface{})
	m["status"] = hc.Status

	if hc.ResponseTimeMs != nil {
		m["response_time_ms"] = *hc.ResponseTimeMs
	}
	if hc.Error != nil {
		m["error"] = *hc.Error
	}
	if hc.Warning != nil {
		m["warning"] = *hc.Warning
	}
	if hc.Info != nil {
		m["info"] = *hc.Info
	}

	for k, v := range hc.AdditionalData {
		m[k] = v
	}

	return marshalMap(m)
}

// DatabaseCheck represents a database health check result.
type DatabaseCheck struct {
	HealthCheck
	PoolSize      *int `json:"pool_size,omitempty"`
	PoolAvailable *int `json:"pool_available,omitempty"`
	PoolMaxSize   *int `json:"pool_max_size,omitempty"`
}

// MemoryCheck represents a memory health check result.
type MemoryCheck struct {
	HealthCheck
	UsedMB              *float64 `json:"used_mb,omitempty"`
	TotalMB             *float64 `json:"total_mb,omitempty"`
	UtilizationPercent  *float64 `json:"utilization_percent,omitempty"`
}

// HealthCheckResponse represents the complete health check response.
type HealthCheckResponse struct {
	Status    HealthStatus           `json:"status"`
	Timestamp time.Time              `json:"timestamp"`
	UptimeMs  int64                  `json:"uptime_ms"`
	Version   string                 `json:"version"`
	Service   string                 `json:"service"`
	Environment string               `json:"environment"`
	ProbeType ProbeType              `json:"probe_type"`
	Checks    map[string]interface{} `json:"checks"`
}

// GetHTTPStatusCode returns the appropriate HTTP status code based on health status and probe type.
func (r *HealthCheckResponse) GetHTTPStatusCode() int {
	if r.Status == StatusDown {
		return 503
	} else if r.Status == StatusInProgress && r.ProbeType == ProbeStartup {
		return 202
	}
	return 200
}

// ComputeOverallStatus computes the overall health status from individual checks.
//
// Logic:
// - If any check is DOWN, overall is DOWN
// - If any check is IN_PROGRESS, overall is IN_PROGRESS
// - If any check is DEGRADED, overall is DEGRADED
// - Otherwise, overall is UP
func ComputeOverallStatus(checks map[string]interface{}) HealthStatus {
	hasDown := false
	hasInProgress := false
	hasDegraded := false

	for _, check := range checks {
		if hc, ok := check.(HealthCheck); ok {
			switch hc.Status {
			case StatusDown:
				hasDown = true
			case StatusInProgress:
				hasInProgress = true
			case StatusDegraded:
				hasDegraded = true
			}
		}
	}

	if hasDown {
		return StatusDown
	} else if hasInProgress {
		return StatusInProgress
	} else if hasDegraded {
		return StatusDegraded
	}
	return StatusUp
}

// Helper function to marshal map to JSON
func marshalMap(m map[string]interface{}) ([]byte, error) {
	// Use encoding/json for simplicity
	// In production code, could use more efficient marshaling
	return []byte("{}"), nil // Placeholder - actual implementation would use json.Marshal
}
