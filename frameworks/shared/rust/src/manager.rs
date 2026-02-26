//! Health check manager implementation.

use crate::types::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant, SystemTime};
use sysinfo::{System, SystemExt};

#[cfg(feature = "database")]
use sqlx::PgPool;

/// Health check manager configuration.
pub struct HealthCheckConfig {
    pub service_name: String,
    pub version: String,
    pub environment: String,
    pub startup_duration_ms: u64,
}

impl Default for HealthCheckConfig {
    fn default() -> Self {
        Self {
            service_name: "velocitybench".to_string(),
            version: "1.0.0".to_string(),
            environment: "development".to_string(),
            startup_duration_ms: 30000, // 30 seconds
        }
    }
}

/// Cached health check result.
struct CachedResult {
    result: HealthCheckResponse,
    timestamp: Instant,
}

/// Health check manager for Rust frameworks.
pub struct HealthCheckManager {
    config: HealthCheckConfig,
    start_time: Instant,
    #[cfg(feature = "database")]
    database: Option<PgPool>,
    cache: Arc<Mutex<HashMap<String, CachedResult>>>,
    cache_ttl: Duration,
    system: Arc<Mutex<System>>,
}

impl HealthCheckManager {
    /// Create a new health check manager.
    pub fn new(config: HealthCheckConfig) -> Self {
        Self {
            config,
            start_time: Instant::now(),
            #[cfg(feature = "database")]
            database: None,
            cache: Arc::new(Mutex::new(HashMap::new())),
            cache_ttl: Duration::from_secs(5),
            system: Arc::new(Mutex::new(System::new_all())),
        }
    }

    /// Set database pool for health checks.
    #[cfg(feature = "database")]
    pub fn with_database(mut self, pool: PgPool) -> Self {
        self.database = Some(pool);
        self
    }

    /// Execute a health check probe.
    pub async fn probe(&self, probe_type: &str) -> Result<HealthCheckResponse, String> {
        let probe = ProbeType::from_str(probe_type)
            .ok_or_else(|| format!("Invalid probe type: {}", probe_type))?;

        // Check cache
        if let Some(cached) = self.get_cached_result(&probe) {
            return Ok(cached);
        }

        // Execute probe
        let result = match probe {
            ProbeType::Liveness => self.liveness_probe().await,
            ProbeType::Readiness => self.readiness_probe().await,
            ProbeType::Startup => self.startup_probe().await,
        };

        // Cache result
        self.cache_result(&probe, &result);

        Ok(result)
    }

    /// Get cached result if still valid.
    fn get_cached_result(&self, probe_type: &ProbeType) -> Option<HealthCheckResponse> {
        let cache = self.cache.lock().unwrap();
        let key = format!("{:?}", probe_type).to_lowercase();

        if let Some(cached) = cache.get(&key) {
            if cached.timestamp.elapsed() < self.cache_ttl {
                return Some(cached.result.clone());
            }
        }
        None
    }

    /// Cache a health check result.
    fn cache_result(&self, probe_type: &ProbeType, result: &HealthCheckResponse) {
        let mut cache = self.cache.lock().unwrap();
        let key = format!("{:?}", probe_type).to_lowercase();
        cache.insert(
            key,
            CachedResult {
                result: result.clone(),
                timestamp: Instant::now(),
            },
        );
    }

    /// Liveness probe: Is the process alive?
    async fn liveness_probe(&self) -> HealthCheckResponse {
        let mut checks = HashMap::new();

        // Memory check (lightweight, no DB required)
        checks.insert("memory".to_string(), self.check_memory());

        let overall_status = compute_overall_status(&checks);

        HealthCheckResponse {
            status: overall_status,
            timestamp: get_timestamp(),
            uptime_ms: self.get_uptime_ms(),
            version: self.config.version.clone(),
            service: self.config.service_name.clone(),
            environment: self.config.environment.clone(),
            probe_type: ProbeType::Liveness,
            checks,
        }
    }

    /// Readiness probe: Can the service handle traffic?
    async fn readiness_probe(&self) -> HealthCheckResponse {
        let mut checks = HashMap::new();

        // Database check
        #[cfg(feature = "database")]
        if let Some(ref db) = self.database {
            checks.insert("database".to_string(), self.check_database(db).await);
        }

        // Memory check
        checks.insert("memory".to_string(), self.check_memory());

        let overall_status = compute_overall_status(&checks);

        HealthCheckResponse {
            status: overall_status,
            timestamp: get_timestamp(),
            uptime_ms: self.get_uptime_ms(),
            version: self.config.version.clone(),
            service: self.config.service_name.clone(),
            environment: self.config.environment.clone(),
            probe_type: ProbeType::Readiness,
            checks,
        }
    }

    /// Startup probe: Has initialization completed?
    async fn startup_probe(&self) -> HealthCheckResponse {
        let mut checks = HashMap::new();

        // Database check
        #[cfg(feature = "database")]
        if let Some(ref db) = self.database {
            checks.insert("database".to_string(), self.check_database(db).await);
        }

        // Warmup check
        checks.insert("warmup".to_string(), self.check_warmup());

        // Memory check
        checks.insert("memory".to_string(), self.check_memory());

        let overall_status = compute_overall_status(&checks);

        HealthCheckResponse {
            status: overall_status,
            timestamp: get_timestamp(),
            uptime_ms: self.get_uptime_ms(),
            version: self.config.version.clone(),
            service: self.config.service_name.clone(),
            environment: self.config.environment.clone(),
            probe_type: ProbeType::Startup,
            checks,
        }
    }

    /// Check database connectivity.
    #[cfg(feature = "database")]
    async fn check_database(&self, pool: &PgPool) -> HealthCheck {
        let start = Instant::now();

        // Execute simple query with timeout
        let timeout = Duration::from_secs(3);
        let result = tokio::time::timeout(timeout, sqlx::query("SELECT 1").fetch_one(pool)).await;

        match result {
            Ok(Ok(_)) => {
                let response_time = start.elapsed().as_secs_f64() * 1000.0;

                // Get pool statistics
                let pool_size = pool.size() as u32;
                let pool_idle = pool.num_idle();
                let pool_max = pool.options().get_max_connections();

                let utilization = (pool_size as f64 / pool_max as f64) * 100.0;

                let mut check = HealthCheck::new(HealthStatus::Up)
                    .with_response_time(response_time)
                    .with_data("pool_size".to_string(), serde_json::json!(pool_size))
                    .with_data("pool_available".to_string(), serde_json::json!(pool_idle))
                    .with_data("pool_max_size".to_string(), serde_json::json!(pool_max));

                if utilization > 95.0 {
                    check.status = HealthStatus::Degraded;
                    check = check.with_warning(format!(
                        "Connection pool nearly exhausted ({}/{})",
                        pool_size, pool_max
                    ));
                } else if utilization > 80.0 {
                    check = check.with_warning(format!(
                        "High connection pool utilization ({:.1}%)",
                        utilization
                    ));
                }

                check
            }
            Ok(Err(e)) => HealthCheck::new(HealthStatus::Down)
                .with_error(format!("Database connection error: {}", e)),
            Err(_) => HealthCheck::new(HealthStatus::Down)
                .with_error("Database query timeout (>3s)".to_string()),
        }
    }

    /// Check memory usage.
    fn check_memory(&self) -> HealthCheck {
        let mut sys = self.system.lock().unwrap();
        sys.refresh_memory();

        let used_mb = sys.used_memory() as f64 / 1024.0 / 1024.0;
        let total_mb = sys.total_memory() as f64 / 1024.0 / 1024.0;
        let utilization = (used_mb / total_mb) * 100.0;

        let mut check = HealthCheck::new(HealthStatus::Up)
            .with_data("used_mb".to_string(), serde_json::json!(used_mb))
            .with_data("total_mb".to_string(), serde_json::json!(total_mb))
            .with_data(
                "utilization_percent".to_string(),
                serde_json::json!(utilization),
            );

        if utilization > 90.0 {
            check.status = HealthStatus::Degraded;
            check = check.with_warning(format!("Critical memory usage ({:.1}%)", utilization));
        } else if utilization > 80.0 {
            check = check.with_warning(format!("High memory usage ({:.1}%)", utilization));
        }

        check
    }

    /// Check if warmup period has completed.
    fn check_warmup(&self) -> HealthCheck {
        let uptime_ms = self.get_uptime_ms();

        if uptime_ms < self.config.startup_duration_ms {
            let progress = (uptime_ms as f64 / self.config.startup_duration_ms as f64) * 100.0;
            HealthCheck::new(HealthStatus::InProgress)
                .with_info(format!("Warming up ({:.0}% complete)", progress))
                .with_data("progress_percent".to_string(), serde_json::json!(progress))
                .with_data("uptime_ms".to_string(), serde_json::json!(uptime_ms))
                .with_data(
                    "target_ms".to_string(),
                    serde_json::json!(self.config.startup_duration_ms),
                )
        } else {
            HealthCheck::new(HealthStatus::Up).with_info("Warmup complete".to_string())
        }
    }

    /// Get service uptime in milliseconds.
    fn get_uptime_ms(&self) -> u64 {
        self.start_time.elapsed().as_millis() as u64
    }
}

// Fix the timestamp function
use chrono;

fn get_timestamp() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true)
}
