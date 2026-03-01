use deadpool_postgres::{Manager, ManagerConfig, Pool, RecyclingMethod};
use std::env;

#[derive(Clone)]
pub struct Database {
    pool: Pool,
}

impl Database {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let mut pg_config = tokio_postgres::Config::new();
        pg_config.host(&env::var("DB_HOST").unwrap_or_else(|_| "localhost".to_string()));
        pg_config.port(
            env::var("DB_PORT")
                .unwrap_or_else(|_| "5432".to_string())
                .parse()?,
        );
        pg_config.user(&env::var("DB_USER").unwrap_or_else(|_| "benchmark".to_string()));
        pg_config.password(&env::var("DB_PASSWORD").unwrap_or_else(|_| "benchmark123".to_string()));
        pg_config.dbname(&env::var("DB_NAME").unwrap_or_else(|_| "velocitybench_benchmark".to_string()));

        let mgr_config = ManagerConfig {
            recycling_method: RecyclingMethod::Fast,
        };
        let mgr = Manager::from_config(pg_config, tokio_postgres::NoTls, mgr_config);

        // Connection pool: min 10, max 50
        let pool = Pool::builder(mgr)
            .max_size(50)
            .build()?;

        Ok(Database { pool })
    }

    pub fn pool(&self) -> &Pool {
        &self.pool
    }
}
