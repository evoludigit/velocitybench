mod db;
mod loaders;
mod models;
mod schema;

use actix_web::{guard, middleware, web, App, HttpResponse, HttpServer};
use juniper_actix::{graphql_handler, playground_handler};
use std::sync::Arc;

use crate::db::Database;
use crate::loaders::Loaders;
use crate::schema::{create_schema, Context, Schema};

/// Health check endpoint
async fn health() -> HttpResponse {
    HttpResponse::Ok()
        .content_type("application/json")
        .body(r#"{"status":"healthy","framework":"juniper"}"#)
}

/// Metrics endpoint (placeholder for Prometheus)
async fn metrics() -> HttpResponse {
    HttpResponse::Ok()
        .content_type("text/plain")
        .body("# HELP juniper_requests_total Total number of GraphQL requests\n# TYPE juniper_requests_total counter\njuniper_requests_total 0\n")
}

/// GraphQL endpoint handler
async fn graphql(
    req: actix_web::HttpRequest,
    payload: actix_web::web::Payload,
    schema: web::Data<Schema>,
    db: web::Data<Database>,
) -> actix_web::Result<HttpResponse> {
    let context = Context {
        db: db.get_ref().clone(),
        loaders: Loaders::new(db.get_ref().clone()),
    };
    graphql_handler(&schema, &context, req, payload).await
}

/// GraphQL Playground handler (disabled for benchmarks but available for testing)
async fn playground() -> actix_web::Result<HttpResponse> {
    playground_handler("/graphql", None).await
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("juniper=info".parse().unwrap())
                .add_directive("actix_web=info".parse().unwrap()),
        )
        .init();

    // Initialize database
    let db = Database::new().expect("Failed to create database connection");

    // Create GraphQL schema
    let schema = Arc::new(create_schema());

    let port = std::env::var("PORT").unwrap_or_else(|_| "4000".to_string());
    let bind_addr = format!("0.0.0.0:{}", port);

    println!("🚀 Juniper GraphQL server starting on http://{}", bind_addr);
    println!("📊 GraphQL endpoint: http://{}/graphql", bind_addr);
    println!("🏥 Health check: http://{}/health", bind_addr);

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::from(schema.clone()))
            .app_data(web::Data::new(db.clone()))
            .wrap(middleware::Logger::default())
            .service(
                web::resource("/graphql")
                    .guard(guard::Post())
                    .to(graphql),
            )
            .service(
                web::resource("/graphql")
                    .guard(guard::Get())
                    .to(playground),
            )
            .service(web::resource("/health").guard(guard::Get()).to(health))
            .service(web::resource("/metrics").guard(guard::Get()).to(metrics))
    })
    .bind(&bind_addr)?
    .run()
    .await
}
