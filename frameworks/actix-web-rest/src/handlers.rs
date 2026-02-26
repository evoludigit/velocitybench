use crate::error::ApiError;
use crate::metrics;
use crate::AppState;
use actix_web::{get, put, web, HttpResponse, Result};
use serde::Deserialize;
use serde_json::json;

// Health check endpoint
#[get("/health")]
pub async fn health() -> HttpResponse {
    HttpResponse::Ok().json(json!({"status": "ok"}))
}

// Metrics endpoint
#[get("/metrics")]
pub async fn metrics_handler() -> Result<HttpResponse, ApiError> {
    match metrics::encode_metrics() {
        Ok(metrics_data) => Ok(HttpResponse::Ok()
            .content_type("text/plain; charset=utf-8")
            .body(metrics_data)),
        Err(e) => Err(ApiError::DatabaseError(format!(
            "Failed to encode metrics: {}",
            e
        ))),
    }
}

// Get single user by ID
#[get("/users/{user_id}")]
pub async fn get_user(
    user_id: web::Path<String>,
    state: web::Data<AppState>,
) -> Result<HttpResponse, ApiError> {
    let user_id = user_id.into_inner();

    let user = state.user_repository.find_by_id(&user_id).await?;

    match user {
        Some(user) => Ok(HttpResponse::Ok().json(user)),
        None => Err(ApiError::NotFound),
    }
}

// List users with pagination and optional eager loading
#[get("/users")]
pub async fn list_users(
    query: web::Query<std::collections::HashMap<String, String>>,
    state: web::Data<AppState>,
) -> Result<HttpResponse, ApiError> {
    let limit: i64 = query
        .get("limit")
        .and_then(|s| s.parse().ok())
        .unwrap_or(10)
        .min(100); // Max 100

    let offset: i64 = query
        .get("offset")
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);

    let users = state.user_repository.find_all(limit, offset).await?;

    Ok(HttpResponse::Ok().json(users))
}

// Get single post by ID with eager-loaded author
#[get("/posts/{post_id}")]
pub async fn get_post(
    post_id: web::Path<String>,
    state: web::Data<AppState>,
) -> Result<HttpResponse, ApiError> {
    let post_id = post_id.into_inner();

    let post = state.post_repository.find_by_id(&post_id).await?;

    match post {
        Some(post) => Ok(HttpResponse::Ok().json(post)),
        None => Err(ApiError::NotFound),
    }
}

// Update user bio
#[derive(Deserialize)]
pub struct UpdateUserPayload {
    pub bio: Option<String>,
}

#[put("/users/{user_id}")]
pub async fn update_user(
    user_id: web::Path<String>,
    body: web::Json<UpdateUserPayload>,
    state: web::Data<AppState>,
) -> Result<HttpResponse, ApiError> {
    let user_id = user_id.into_inner();
    let bio = body.bio.as_deref().unwrap_or("");
    let user = state.user_repository.update_bio(&user_id, bio).await?;
    Ok(HttpResponse::Ok().json(user))
}

// List posts with pagination, eager-loaded authors, and optional comments
#[get("/posts")]
pub async fn list_posts(
    query: web::Query<std::collections::HashMap<String, String>>,
    state: web::Data<AppState>,
) -> Result<HttpResponse, ApiError> {
    let limit: i64 = query
        .get("limit")
        .and_then(|s| s.parse().ok())
        .unwrap_or(10)
        .min(100);

    let offset: i64 = query
        .get("offset")
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);

    let include_author = query.get("include").map(|s| s == "author").unwrap_or(false);

    let posts = if include_author {
        state.post_repository.find_all_with_author(limit, offset).await?
    } else {
        state.post_repository.find_all_simple(limit, offset).await?
    };

    Ok(HttpResponse::Ok().json(posts))
}
