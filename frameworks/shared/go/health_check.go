package healthcheck

import (
	"context"
	"database/sql"
	"fmt"
	"runtime"
	"sync"
	"time"
)

// HealthCheckManager manages health checks for a VelocityBench Go framework.
type HealthCheckManager struct {
	serviceName       string
	version           string
	environment       string
	database          *sql.DB
	startupDurationMs int64
	startTime         time.Time
	cache             sync.Map
	cacheTTL          time.Duration
}

type cachedResult struct {
	result    *HealthCheckResponse
	timestamp time.Time
}

// Config holds configuration for the health check manager.
type Config struct {
	ServiceName       string
	Version           string
	Environment       string
	Database          *sql.DB
	StartupDurationMs int64 // Warmup period in milliseconds
}

// New creates a new HealthCheckManager.
func New(config Config) *HealthCheckManager {
	if config.Environment == "" {
		config.Environment = "development"
	}
	if config.StartupDurationMs == 0 {
		config.StartupDurationMs = 30000 // 30 seconds default
	}

	return &HealthCheckManager{
		serviceName:       config.ServiceName,
		version:           config.Version,
		environment:       config.Environment,
		database:          config.Database,
		startupDurationMs: config.StartupDurationMs,
		startTime:         time.Now(),
		cacheTTL:          5 * time.Second,
	}
}

// Probe executes a health check probe.
func (m *HealthCheckManager) Probe(probeType string) (*HealthCheckResponse, error) {
	var probe ProbeType
	switch probeType {
	case "liveness":
		probe = ProbeLiveness
	case "readiness":
		probe = ProbeReadiness
	case "startup":
		probe = ProbeStartup
	default:
		return nil, fmt.Errorf("invalid probe type: %s", probeType)
	}

	// Check cache
	if cached := m.getCachedResult(probe); cached != nil {
		return cached, nil
	}

	// Execute probe
	var result *HealthCheckResponse
	switch probe {
	case ProbeLiveness:
		result = m.livenessProbe()
	case ProbeReadiness:
		result = m.readinessProbe()
	case ProbeStartup:
		result = m.startupProbe()
	}

	// Cache result
	m.cache.Store(string(probe), cachedResult{
		result:    result,
		timestamp: time.Now(),
	})

	return result, nil
}

// getCachedResult retrieves a cached health check result if still valid.
func (m *HealthCheckManager) getCachedResult(probeType ProbeType) *HealthCheckResponse {
	if cached, ok := m.cache.Load(string(probeType)); ok {
		if cr, ok := cached.(cachedResult); ok {
			if time.Since(cr.timestamp) < m.cacheTTL {
				return cr.result
			}
		}
	}
	return nil
}

// livenessProbe checks if the process is alive.
//
// Checks:
// - Process is running
// - Memory is accessible
//
// Does NOT check database or external dependencies.
func (m *HealthCheckManager) livenessProbe() *HealthCheckResponse {
	checks := make(map[string]interface{})

	// Memory check (lightweight, no DB required)
	checks["memory"] = m.checkMemory()

	overallStatus := m.computeOverallStatus(checks)

	return &HealthCheckResponse{
		Status:      overallStatus,
		Timestamp:   time.Now().UTC(),
		UptimeMs:    m.getUptimeMs(),
		Version:     m.version,
		Service:     m.serviceName,
		Environment: m.environment,
		ProbeType:   ProbeLiveness,
		Checks:      checks,
	}
}

// readinessProbe checks if the service can handle traffic.
//
// Checks:
// - Process is running
// - Database connection is healthy
// - Memory usage is acceptable
func (m *HealthCheckManager) readinessProbe() *HealthCheckResponse {
	checks := make(map[string]interface{})

	// Database check
	if m.database != nil {
		checks["database"] = m.checkDatabase()
	}

	// Memory check
	checks["memory"] = m.checkMemory()

	overallStatus := m.computeOverallStatus(checks)

	return &HealthCheckResponse{
		Status:      overallStatus,
		Timestamp:   time.Now().UTC(),
		UptimeMs:    m.getUptimeMs(),
		Version:     m.version,
		Service:     m.serviceName,
		Environment: m.environment,
		ProbeType:   ProbeReadiness,
		Checks:      checks,
	}
}

// startupProbe checks if initialization is complete.
//
// Checks:
// - Process is running
// - Database connection established
// - Warmup period finished
func (m *HealthCheckManager) startupProbe() *HealthCheckResponse {
	checks := make(map[string]interface{})

	// Database check
	if m.database != nil {
		checks["database"] = m.checkDatabase()
	}

	// Warmup check
	checks["warmup"] = m.checkWarmup()

	// Memory check
	checks["memory"] = m.checkMemory()

	overallStatus := m.computeOverallStatus(checks)

	return &HealthCheckResponse{
		Status:      overallStatus,
		Timestamp:   time.Now().UTC(),
		UptimeMs:    m.getUptimeMs(),
		Version:     m.version,
		Service:     m.serviceName,
		Environment: m.environment,
		ProbeType:   ProbeStartup,
		Checks:      checks,
	}
}

// checkDatabase checks database connectivity and health.
func (m *HealthCheckManager) checkDatabase() HealthCheck {
	if m.database == nil {
		errMsg := "Database not initialized"
		return HealthCheck{
			Status: StatusDown,
			Error:  &errMsg,
		}
	}

	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	// Execute simple query to verify connectivity
	var result int
	err := m.database.QueryRowContext(ctx, "SELECT 1").Scan(&result)

	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			errMsg := "Database query timeout (>3s)"
			return HealthCheck{
				Status: StatusDown,
				Error:  &errMsg,
			}
		}
		errMsg := fmt.Sprintf("Database connection error: %v", err)
		return HealthCheck{
			Status: StatusDown,
			Error:  &errMsg,
		}
	}

	responseTime := float64(time.Since(start).Milliseconds())

	// Get pool statistics (if available)
	stats := m.database.Stats()
	poolSize := stats.OpenConnections
	poolMaxSize := stats.MaxOpenConnections
	poolIdle := stats.Idle

	// Calculate utilization
	var utilization float64
	if poolMaxSize > 0 {
		utilization = (float64(poolSize) / float64(poolMaxSize)) * 100
	}

	status := StatusUp
	var warning *string

	if utilization > 95 {
		status = StatusDegraded
		warnMsg := fmt.Sprintf("Connection pool nearly exhausted (%d/%d)", poolSize, poolMaxSize)
		warning = &warnMsg
	} else if utilization > 80 {
		warnMsg := fmt.Sprintf("High connection pool utilization (%.1f%%)", utilization)
		warning = &warnMsg
	}

	return HealthCheck{
		Status:         status,
		ResponseTimeMs: &responseTime,
		Warning:        warning,
		AdditionalData: map[string]interface{}{
			"pool_size":      poolSize,
			"pool_available": poolIdle,
			"pool_max_size":  poolMaxSize,
		},
	}
}

// checkMemory checks memory usage.
func (m *HealthCheckManager) checkMemory() HealthCheck {
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	usedMB := float64(memStats.Alloc) / 1024 / 1024
	totalMB := float64(memStats.Sys) / 1024 / 1024
	utilization := (usedMB / totalMB) * 100

	status := StatusUp
	var warning *string

	if utilization > 90 {
		status = StatusDegraded
		warnMsg := fmt.Sprintf("Critical memory usage (%.1f%%)", utilization)
		warning = &warnMsg
	} else if utilization > 80 {
		warnMsg := fmt.Sprintf("High memory usage (%.1f%%)", utilization)
		warning = &warnMsg
	}

	return HealthCheck{
		Status:  status,
		Warning: warning,
		AdditionalData: map[string]interface{}{
			"used_mb":             usedMB,
			"total_mb":            totalMB,
			"utilization_percent": utilization,
		},
	}
}

// checkWarmup checks if warmup period has completed.
func (m *HealthCheckManager) checkWarmup() HealthCheck {
	uptimeMs := m.getUptimeMs()

	if uptimeMs < m.startupDurationMs {
		progress := (float64(uptimeMs) / float64(m.startupDurationMs)) * 100
		infoMsg := fmt.Sprintf("Warming up (%.0f%% complete)", progress)
		return HealthCheck{
			Status: StatusInProgress,
			Info:   &infoMsg,
			AdditionalData: map[string]interface{}{
				"progress_percent": progress,
				"uptime_ms":        uptimeMs,
				"target_ms":        m.startupDurationMs,
			},
		}
	}

	infoMsg := "Warmup complete"
	return HealthCheck{
		Status: StatusUp,
		Info:   &infoMsg,
	}
}

// computeOverallStatus computes overall health status from checks.
func (m *HealthCheckManager) computeOverallStatus(checks map[string]interface{}) HealthStatus {
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

// getUptimeMs returns service uptime in milliseconds.
func (m *HealthCheckManager) getUptimeMs() int64 {
	return time.Since(m.startTime).Milliseconds()
}
