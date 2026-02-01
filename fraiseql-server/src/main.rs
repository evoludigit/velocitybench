use anyhow::Result;
use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use clap::Parser;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tracing::info;

/// FraiseQL Server - Compiled GraphQL execution engine
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to schema.json file
    #[arg(long)]
    schema: std::path::PathBuf,

    /// Port to listen on
    #[arg(long, default_value = "8080")]
    port: u16,

    /// Database URL
    #[arg(long, default_value = "sqlite:memory:")]
    database_url: String,
}

#[derive(Clone)]
struct AppState {
    // Schema will be used in Cycle 2 for query validation and execution
    #[allow(dead_code)]
    schema: Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct GraphQLRequest {
    query: String,
    #[serde(default)]
    variables: Value,
    #[serde(default)]
    operation_name: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GraphQLResponse {
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    errors: Option<Vec<ErrorDetail>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ErrorDetail {
    message: String,
}

async fn health() -> impl IntoResponse {
    Json(json!({"status": "ok"}))
}

async fn graphql(
    State(_state): State<Arc<AppState>>,
    Json(req): Json<GraphQLRequest>,
) -> impl IntoResponse {
    // For now, return a placeholder response
    // In production, this would parse the query, validate against schema,
    // and execute against the database
    info!("Received GraphQL query: {}", req.query);

    // Placeholder: return empty data
    let response = GraphQLResponse {
        data: Some(json!({})),
        errors: None,
    };

    (StatusCode::OK, Json(response))
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    let args = Args::parse();
    info!("Starting FraiseQL Server");
    info!("Schema: {}", args.schema.display());
    info!("Database: {}", args.database_url);

    // Load schema
    let schema_content = std::fs::read_to_string(&args.schema)?;
    let schema: Value = serde_json::from_str(&schema_content)?;
    info!("Schema loaded successfully");

    let state = Arc::new(AppState { schema });

    // Build router
    let router = Router::new()
        .route("/health", get(health))
        .route("/graphql", post(graphql))
        .with_state(state);

    // Start server
    let listener = tokio::net::TcpListener::bind(format!("127.0.0.1:{}", args.port)).await?;
    info!("Server listening on http://127.0.0.1:{}", args.port);

    axum::serve(listener, router).await?;

    Ok(())
}
