//! Type definitions for VelocityBench health checks.
//!
//! Provides standardized types for health check responses compatible
//! with Kubernetes probes (liveness, readiness, startup).

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::SystemTime;

/// Health check status values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HealthStatus {
    /// Service or check is healthy.
    Up,
    /// Service is functional but with warnings.
    Degraded,
    /// Service or check is unhealthy.
    Down,
    /// Initialization is in progress (startup probe).
    InProgress,
}

/// Health check probe types (Kubernetes-compatible).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProbeType {
    /// Liveness probe - Is the process alive?
    Liveness,
    /// Readiness probe - Can the service handle traffic?
    Readiness,
    /// Startup probe - Has initialization completed?
    Startup,
}

impl ProbeType {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "liveness" => Some(ProbeType::Liveness),
            "readiness" => Some(ProbeType::Readiness),
            "startup" => Some(ProbeType::Startup),
            _ => None,
        }
    }
}

/// Individual health check result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheck {
    pub status: HealthStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub response_time_ms: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub warning: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub info: Option<String>,
    #[serde(flatten)]
    pub additional_data: HashMap<String, serde_json::Value>,
}

impl HealthCheck {
    pub fn new(status: HealthStatus) -> Self {
        Self {
            status,
            response_time_ms: None,
            error: None,
            warning: None,
            info: None,
            additional_data: HashMap::new(),
        }
    }

    pub fn with_error(mut self, error: String) -> Self {
        self.error = Some(error);
        self
    }

    pub fn with_warning(mut self, warning: String) -> Self {
        self.warning = Some(warning);
        self
    }

    pub fn with_info(mut self, info: String) -> Self {
        self.info = Some(info);
        self
    }

    pub fn with_response_time(mut self, ms: f64) -> Self {
        self.response_time_ms = Some(ms);
        self
    }

    pub fn with_data(mut self, key: String, value: serde_json::Value) -> Self {
        self.additional_data.insert(key, value);
        self
    }
}

/// Complete health check response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub status: HealthStatus,
    pub timestamp: String,
    pub uptime_ms: u64,
    pub version: String,
    pub service: String,
    pub environment: String,
    pub probe_type: ProbeType,
    pub checks: HashMap<String, HealthCheck>,
}

impl HealthCheckResponse {
    /// Get HTTP status code based on health status and probe type.
    pub fn http_status_code(&self) -> u16 {
        match self.status {
            HealthStatus::Down => 503,
            HealthStatus::InProgress if self.probe_type == ProbeType::Startup => 202,
            _ => 200,
        }
    }
}

/// Compute overall health status from individual checks.
///
/// Logic:
/// - If any check is DOWN, overall is DOWN
/// - If any check is IN_PROGRESS, overall is IN_PROGRESS
/// - If any check is DEGRADED, overall is DEGRADED
/// - Otherwise, overall is UP
pub fn compute_overall_status(checks: &HashMap<String, HealthCheck>) -> HealthStatus {
    let mut has_down = false;
    let mut has_in_progress = false;
    let mut has_degraded = false;

    for check in checks.values() {
        match check.status {
            HealthStatus::Down => has_down = true,
            HealthStatus::InProgress => has_in_progress = true,
            HealthStatus::Degraded => has_degraded = true,
            HealthStatus::Up => {}
        }
    }

    if has_down {
        HealthStatus::Down
    } else if has_in_progress {
        HealthStatus::InProgress
    } else if has_degraded {
        HealthStatus::Degraded
    } else {
        HealthStatus::Up
    }
}

/// Get current timestamp in ISO 8601 format (UTC).
pub fn get_timestamp() -> String {
    let now = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap();

    // Simple ISO 8601 formatting
    let secs = now.as_secs();
    let millis = now.subsec_millis();

    // Format as ISO 8601
    chrono::DateTime::from_timestamp(secs as i64, millis * 1_000_000)
        .unwrap()
        .format("%Y-%m-%dT%H:%M:%S%.3fZ")
        .to_string()
}
