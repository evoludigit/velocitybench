mod dataloaders;
mod db;
mod models;
mod schema;

use actix_web::{guard, web, App, HttpServer};
use async_graphql::http::GraphiQLSource;
use async_graphql_actix_web::{GraphQLRequest, GraphQLResponse};
use async_graphql::{EmptySubscription, Schema};

async fn graphiql() -> actix_web::Result<actix_web::HttpResponse> {
    Ok(actix_web::HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(GraphiQLSource::build().endpoint("/graphql").finish()))
}

async fn graphql_handler(
    schema: web::Data<Schema<schema::QueryRoot, schema::MutationRoot, EmptySubscription>>,
    req: GraphQLRequest,
) -> GraphQLResponse {
    schema.execute(req.into_inner()).await.into()
}

async fn health() -> actix_web::Result<actix_web::HttpResponse> {
    Ok(actix_web::HttpResponse::Ok()
        .content_type("application/json")
        .body(r#"{"status":"ok"}"#))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Initialize database
    let db = db::Database::new().expect("Failed to create database connection");

    // Create DataLoaders
    let user_loader = async_graphql::dataloader::DataLoader::new(
        dataloaders::UserLoader::new(db.clone()),
        tokio::spawn,
    );
    let post_loader = async_graphql::dataloader::DataLoader::new(
        dataloaders::PostLoader::new(db.clone()),
        tokio::spawn,
    );
    let posts_by_author_loader = async_graphql::dataloader::DataLoader::new(
        dataloaders::PostsByAuthorLoader::new(db.clone()),
        tokio::spawn,
    );
    let comments_by_post_loader = async_graphql::dataloader::DataLoader::new(
        dataloaders::CommentsByPostLoader::new(db.clone()),
        tokio::spawn,
    );
    let comment_loader = async_graphql::dataloader::DataLoader::new(
        dataloaders::CommentLoader::new(db.clone()),
        tokio::spawn,
    );

    // Create GraphQL schema
    let query_root = schema::QueryRoot::new(db.clone());
    let mutation_root = schema::MutationRoot::new(db.clone());
    let schema = Schema::build(query_root, mutation_root, EmptySubscription)
        .data(db.clone())
        .data(user_loader)
        .data(post_loader)
        .data(posts_by_author_loader)
        .data(comments_by_post_loader)
        .data(comment_loader)
        .finish();

    println!("🚀 GraphQL server starting on http://localhost:8000");
    println!("📊 GraphQL Playground available at http://localhost:8000/graphiql");

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(schema.clone()))
            .app_data(web::Data::new(db.clone()))
            .service(
                web::resource("/graphql")
                    .guard(guard::Post())
                    .to(graphql_handler),
            )
            .service(
                web::resource("/graphiql")
                    .guard(guard::Get())
                    .to(graphiql),
            )
            .service(
                web::resource("/health")
                    .guard(guard::Get())
                    .to(health),
            )
    })
    .bind("0.0.0.0:8000")?
    .run()
    .await
}
