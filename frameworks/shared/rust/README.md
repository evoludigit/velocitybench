# VelocityBench Rust Health Check Library

Standardized health check library for VelocityBench Rust frameworks.

## Features

- **Kubernetes-compatible probes**: Liveness, readiness, and startup
- **Database health checks**: SQLx integration for PostgreSQL
- **Memory monitoring**: System memory statistics via sysinfo
- **Framework integrations**: Actix-web, Axum support
- **Async/await**: Full async support with Tokio

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
velocitybench-healthcheck = { path = "../shared/rust" }

# Enable features as needed
velocitybench-healthcheck = { path = "../shared/rust", features = ["actix", "database"] }
```

### Features

- `actix` - Actix-web integration
- `axum_support` - Axum integration
- `database` - Database health checks with SQLx

## Usage

### Basic Usage

```rust
use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};

#[tokio::main]
async fn main() {
    let config = HealthCheckConfig {
        service_name: "my-service".to_string(),
        version: "1.0.0".to_string(),
        environment: "production".to_string(),
        startup_duration_ms: 30000,
    };

    let health_manager = HealthCheckManager::new(config);

    // Execute health check
    let result = health_manager.probe("readiness").await.unwrap();
    println!("Status: {:?}", result.status);
    println!("HTTP Status Code: {}", result.http_status_code());
}
```

### With Database

```rust
use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};
use sqlx::PgPool;

#[tokio::main]
async fn main() {
    // Create database pool
    let pool = PgPool::connect("postgres://localhost/mydb").await.unwrap();

    let config = HealthCheckConfig {
        service_name: "my-service".to_string(),
        version: "1.0.0".to_string(),
        environment: "production".to_string(),
        startup_duration_ms: 30000,
    };

    let health_manager = HealthCheckManager::new(config)
        .with_database(pool);

    let result = health_manager.probe("readiness").await.unwrap();
}
```

### With Actix-web

```rust
use actix_web::{web, App, HttpServer};
use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let config = HealthCheckConfig::default();
    let health_manager = web::Data::new(HealthCheckManager::new(config));

    HttpServer::new(move || {
        App::new()
            .app_data(health_manager.clone())
            .route("/health", web::get().to(health_endpoint))
            .route("/health/live", web::get().to(health_live))
            .route("/health/ready", web::get().to(health_ready))
            .route("/health/startup", web::get().to(health_startup))
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}

async fn health_endpoint(manager: web::Data<HealthCheckManager>) -> impl Responder {
    match manager.probe("readiness").await {
        Ok(result) => HttpResponse::build(StatusCode::from_u16(result.http_status_code()).unwrap())
            .json(result),
        Err(e) => HttpResponse::ServiceUnavailable().json(json!({"error": e})),
    }
}
```

### With Axum

```rust
use axum::{routing::get, Router, Json};
use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};
use std::sync::Arc;

#[tokio::main]
async fn main() {
    let config = HealthCheckConfig::default();
    let health_manager = Arc::new(HealthCheckManager::new(config));

    let app = Router::new()
        .route("/health", get(health_endpoint))
        .route("/health/live", get(health_live))
        .route("/health/ready", get(health_ready))
        .route("/health/startup", get(health_startup))
        .with_state(health_manager);

    axum::Server::bind(&"0.0.0.0:8080".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn health_endpoint(
    State(manager): State<Arc<HealthCheckManager>>,
) -> Result<Json<HealthCheckResponse>, StatusCode> {
    match manager.probe("readiness").await {
        Ok(result) => Ok(Json(result)),
        Err(_) => Err(StatusCode::SERVICE_UNAVAILABLE),
    }
}
```

## Response Format

```json
{
  "status": "up",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 3456789,
  "version": "1.0.0",
  "service": "my-service",
  "environment": "production",
  "probe_type": "readiness",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5.2,
      "pool_size": 10,
      "pool_available": 8,
      "pool_max_size": 20
    },
    "memory": {
      "status": "up",
      "used_mb": 45.3,
      "total_mb": 2048.0,
      "utilization_percent": 2.2
    }
  }
}
```

## License

MIT
