mod db;
mod error;
mod handlers;
mod metrics;
mod models;
mod repositories;

use actix_web::{web, App, HttpServer};
use crate::repositories::{CommentRepository, PostRepository, UserRepository};
use std::env;

#[derive(Clone)]
pub struct AppState {
    pub user_repository: UserRepository,
    pub post_repository: PostRepository,
    pub comment_repository: CommentRepository,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Actix-web REST Framework - Starting server");

    // Initialize metrics
    if let Err(e) = metrics::init_metrics() {
        println!("❌ Failed to initialize metrics: {}", e);
        return Err(std::io::Error::new(
            std::io::ErrorKind::Other,
            e.to_string(),
        ));
    }
    println!("✅ Metrics initialized");

    // Initialize database connection
    let pool = db::create_pool();
    match db::init_db().await {
        Ok(_) => println!("✅ Database connection successful"),
        Err(e) => {
            println!("❌ Database connection failed: {}", e);
            println!("Make sure PostgreSQL is running on localhost:5434");
            println!("Or set DATABASE_URL environment variable");
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                e.to_string(),
            ));
        }
    }

    // Create repositories
    let user_repository = UserRepository::new(pool.clone());
    let post_repository = PostRepository::new(pool.clone());
    let comment_repository = CommentRepository::new(pool.clone());

    let app_state = AppState {
        user_repository,
        post_repository,
        comment_repository,
    };

    let port = env::var("PORT").unwrap_or_else(|_| "8002".to_string());
    let bind_addr = format!("0.0.0.0:{}", port);

    println!("🚀 Starting server on http://{}", bind_addr);
    println!("📊 Health check: http://{}:{}/health", "localhost", port);

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(app_state.clone()))
            .service(handlers::health)
            .service(handlers::get_user)
            .service(handlers::list_users)
            .service(handlers::get_post)
            .service(handlers::list_posts)
            .service(handlers::metrics_handler)
    })
    .bind(&bind_addr)?
    .run()
    .await
}
