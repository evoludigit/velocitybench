use deadpool_postgres::{Manager, ManagerConfig, Pool, RecyclingMethod};

#[derive(Clone)]
pub struct Database {
    pool: Pool,
}

impl Database {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let mut pg_config = tokio_postgres::Config::new();
        pg_config.host(std::env::var("DATABASE_HOST").unwrap_or_else(|_| "localhost".to_string()));
        pg_config.port(std::env::var("DATABASE_PORT")
            .unwrap_or_else(|_| "5434".to_string())
            .parse()?);
        pg_config.user(std::env::var("DATABASE_USER").unwrap_or_else(|_| "benchmark".to_string()));
        pg_config.password(std::env::var("DATABASE_PASSWORD").unwrap_or_else(|_| "benchmark123".to_string()));
        pg_config.dbname(std::env::var("DATABASE_NAME").unwrap_or_else(|_| "fraiseql_benchmark".to_string()));

        let mgr_config = ManagerConfig {
            recycling_method: RecyclingMethod::Fast,
        };
        let mgr = Manager::from_config(pg_config, tokio_postgres::NoTls, mgr_config);
        let pool = Pool::builder(mgr).max_size(20).build()?;

        Ok(Database { pool })
    }

    pub fn pool(&self) -> &Pool {
        &self.pool
    }
}