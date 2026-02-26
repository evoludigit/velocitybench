//! Actix-web integration for health checks.

use crate::{HealthCheckManager, HealthCheckResponse};
use actix_web::{web, HttpResponse, Responder};

/// Health check handler for Actix-web.
///
/// Returns JSON response with appropriate HTTP status code.
pub async fn health_handler(
    manager: web::Data<HealthCheckManager>,
    probe_type: web::Path<String>,
) -> impl Responder {
    match manager.probe(&probe_type).await {
        Ok(result) => {
            let status_code = result.http_status_code();
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(result)
        }
        Err(e) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": e
        })),
    }
}

/// Combined health check endpoint (defaults to readiness).
pub async fn health_endpoint(manager: web::Data<HealthCheckManager>) -> impl Responder {
    match manager.probe("readiness").await {
        Ok(result) => {
            let status_code = result.http_status_code();
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(result)
        }
        Err(e) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": e
        })),
    }
}

/// Liveness probe endpoint.
pub async fn health_live(manager: web::Data<HealthCheckManager>) -> impl Responder {
    match manager.probe("liveness").await {
        Ok(result) => {
            let status_code = result.http_status_code();
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(result)
        }
        Err(e) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": e
        })),
    }
}

/// Readiness probe endpoint.
pub async fn health_ready(manager: web::Data<HealthCheckManager>) -> impl Responder {
    match manager.probe("readiness").await {
        Ok(result) => {
            let status_code = result.http_status_code();
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(result)
        }
        Err(e) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": e
        })),
    }
}

/// Startup probe endpoint.
pub async fn health_startup(manager: web::Data<HealthCheckManager>) -> impl Responder {
    match manager.probe("startup").await {
        Ok(result) => {
            let status_code = result.http_status_code();
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(result)
        }
        Err(e) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "error": e
        })),
    }
}

/// Configure health check routes on an Actix-web app.
///
/// # Example
///
/// ```rust
/// use actix_web::{web, App, HttpServer};
/// use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};
/// use velocitybench_healthcheck::actix::configure_health_routes;
///
/// #[actix_web::main]
/// async fn main() -> std::io::Result<()> {
///     let config = HealthCheckConfig::default();
///     let health_manager = web::Data::new(HealthCheckManager::new(config));
///
///     HttpServer::new(move || {
///         App::new()
///             .app_data(health_manager.clone())
///             .configure(configure_health_routes)
///     })
///     .bind(("127.0.0.1", 8080))?
///     .run()
///     .await
/// }
/// ```
pub fn configure_health_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/health")
            .route("", web::get().to(health_endpoint))
            .route("/live", web::get().to(health_live))
            .route("/ready", web::get().to(health_ready))
            .route("/startup", web::get().to(health_startup)),
    );
}
