//! Axum integration for health checks.

use crate::{HealthCheckManager, HealthCheckResponse};
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use std::sync::Arc;

/// Health check response wrapper for Axum.
pub struct HealthResponse(pub HealthCheckResponse);

impl IntoResponse for HealthResponse {
    fn into_response(self) -> Response {
        let status_code = self.0.http_status_code();
        let status = StatusCode::from_u16(status_code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR);
        (status, Json(self.0)).into_response()
    }
}

/// Combined health check endpoint (defaults to readiness).
pub async fn health_endpoint(
    State(manager): State<Arc<HealthCheckManager>>,
) -> Result<HealthResponse, StatusCode> {
    match manager.probe("readiness").await {
        Ok(result) => Ok(HealthResponse(result)),
        Err(_) => Err(StatusCode::SERVICE_UNAVAILABLE),
    }
}

/// Liveness probe endpoint.
pub async fn health_live(
    State(manager): State<Arc<HealthCheckManager>>,
) -> Result<HealthResponse, StatusCode> {
    match manager.probe("liveness").await {
        Ok(result) => Ok(HealthResponse(result)),
        Err(_) => Err(StatusCode::SERVICE_UNAVAILABLE),
    }
}

/// Readiness probe endpoint.
pub async fn health_ready(
    State(manager): State<Arc<HealthCheckManager>>,
) -> Result<HealthResponse, StatusCode> {
    match manager.probe("readiness").await {
        Ok(result) => Ok(HealthResponse(result)),
        Err(_) => Err(StatusCode::SERVICE_UNAVAILABLE),
    }
}

/// Startup probe endpoint.
pub async fn health_startup(
    State(manager): State<Arc<HealthCheckManager>>,
) -> Result<HealthResponse, StatusCode> {
    match manager.probe("startup").await {
        Ok(result) => Ok(HealthResponse(result)),
        Err(_) => Err(StatusCode::SERVICE_UNAVAILABLE),
    }
}

/// Create health check routes for Axum.
///
/// # Example
///
/// ```rust
/// use axum::{Router, routing::get};
/// use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};
/// use velocitybench_healthcheck::axum_support;
/// use std::sync::Arc;
///
/// #[tokio::main]
/// async fn main() {
///     let config = HealthCheckConfig::default();
///     let health_manager = Arc::new(HealthCheckManager::new(config));
///
///     let app = Router::new()
///         .nest("/health", axum_support::health_routes())
///         .with_state(health_manager);
///
///     let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
///     axum::serve(listener, app).await.unwrap();
/// }
/// ```
pub fn health_routes() -> axum::Router<Arc<HealthCheckManager>> {
    axum::Router::new()
        .route("/", axum::routing::get(health_endpoint))
        .route("/live", axum::routing::get(health_live))
        .route("/ready", axum::routing::get(health_ready))
        .route("/startup", axum::routing::get(health_startup))
}
