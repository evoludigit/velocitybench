use deadpool_postgres::tokio_postgres::NoTls;
use deadpool_postgres::{Config, ManagerConfig, Pool, RecyclingMethod};
use std::env;

pub type DbPool = Pool;

pub fn create_pool() -> DbPool {
    let mut cfg = Config::new();

    // Check for DATABASE_URL first (for local development)
    if let Ok(db_url) = env::var("DATABASE_URL") {
        cfg.url = Some(db_url);
    } else {
        // Use individual environment variables (for docker-compose)
        cfg.dbname = Some(env::var("DB_NAME").unwrap_or_else(|_| "fraiseql_benchmark".to_string()));
        cfg.user = Some(env::var("DB_USER").unwrap_or_else(|_| "benchmark".to_string()));
        cfg.password = Some(env::var("DB_PASSWORD").unwrap_or_else(|_| "benchmark123".to_string()));
        cfg.host = Some(env::var("DB_HOST").unwrap_or_else(|_| "localhost".to_string()));
        cfg.port = Some(
            env::var("DB_PORT")
                .unwrap_or_else(|_| "5434".to_string())
                .parse()
                .unwrap_or(5434),
        );
    }

    // Configure connection pool
    cfg.manager = Some(ManagerConfig {
        recycling_method: RecyclingMethod::Fast,
    });

    // Create pool with min/max connections
    let _pool_size_min = env::var("DB_POOL_MIN")
        .unwrap_or_else(|_| "20".to_string())
        .parse::<usize>()
        .unwrap_or(20);

    let _pool_size_max = env::var("DB_POOL_MAX")
        .unwrap_or_else(|_| "100".to_string())
        .parse::<usize>()
        .unwrap_or(100);

    cfg.create_pool(Some(deadpool_postgres::Runtime::Tokio1), NoTls)
        .expect("Failed to create database pool")
}

pub async fn init_db() -> Result<(), Box<dyn std::error::Error>> {
    let pool = create_pool();

    // Test connection
    let client = pool.get().await?;
    println!("Database connection established");

    // Check if required tables exist
    let tables_exist = client
        .query_one(
            "SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'benchmark'
                AND table_name IN ('tb_user', 'tb_post', 'tb_comment')
            )",
            &[],
        )
        .await?;

    let tables_exist: bool = tables_exist.get(0);

    if tables_exist {
        println!("Required tables exist in benchmark schema");
    } else {
        println!("Warning: Required tables may not exist. Please ensure database is initialized.");
    }

    Ok(())
}
