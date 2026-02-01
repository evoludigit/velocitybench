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
    // In production, this would parse the query, validate against schema,
    // and execute against the database using pre-compiled queries
    info!("Received GraphQL query: {}", req.query);

    // For Cycle 2: Return mock data that matches the query structure
    let data = generate_mock_response(&req.query);

    let response = GraphQLResponse {
        data: Some(data),
        errors: None,
    };

    (StatusCode::OK, Json(response))
}

/// Generate mock response data based on query structure
fn generate_mock_response(query: &str) -> Value {
    // Check what fields are requested
    let mut response = json!({});

    if query.contains("users") {
        response["users"] = json!([
            { "id": "1", "name": "Alice", "email": "alice@example.com" },
            { "id": "2", "name": "Bob", "email": "bob@example.com" },
        ]);
    }

    if query.contains("posts") {
        response["posts"] = json!([
            { "id": "1", "title": "First Post", "author_id": "1" },
            { "id": "2", "title": "Second Post", "author_id": "2" },
        ]);
    }

    if query.contains("create_user") {
        response["create_user"] = json!({
            "id": "3",
            "name": "Test User",
            "email": "test@example.com"
        });
    }

    response
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
