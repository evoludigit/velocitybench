//! VelocityBench Health Check Library for Rust
//!
//! Provides standardized health check functionality for Rust frameworks
//! with Kubernetes-compatible probes (liveness, readiness, startup).
//!
//! # Features
//!
//! - `actix` - Enable Actix-web integration
//! - `axum_support` - Enable Axum integration
//! - `database` - Enable database health checks with SQLx
//!
//! # Examples
//!
//! ```rust
//! use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};
//!
//! #[tokio::main]
//! async fn main() {
//!     let config = HealthCheckConfig {
//!         service_name: "my-service".to_string(),
//!         version: "1.0.0".to_string(),
//!         environment: "production".to_string(),
//!         startup_duration_ms: 30000,
//!     };
//!
//!     let health_manager = HealthCheckManager::new(config);
//!
//!     let result = health_manager.probe("readiness").await.unwrap();
//!     println!("Health status: {:?}", result.status);
//! }
//! ```

pub mod types;
pub mod manager;

#[cfg(feature = "actix")]
pub mod actix;

#[cfg(feature = "axum_support")]
pub mod axum_support;

pub use types::*;
pub use manager::{HealthCheckManager, HealthCheckConfig};
