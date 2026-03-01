package db

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

var Pool *pgxpool.Pool

func Init() error {
	connStr := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?pool_min_conns=10&pool_max_conns=100",
		getEnv("DB_USER", "benchmark"),
		getEnv("DB_PASSWORD", "benchmark123"),
		getEnv("DB_HOST", "postgres"),
		getEnv("DB_PORT", "5432"),
		getEnv("DB_NAME", "velocitybench_benchmark"),
	)

	config, err := pgxpool.ParseConfig(connStr)
	if err != nil {
		return fmt.Errorf("parse config: %w", err)
	}

	// Connection pool settings
	config.MinConns = 10
	config.MaxConns = 100
	config.MaxConnLifetime = 30 * time.Minute
	config.MaxConnIdleTime = 5 * time.Minute
	config.HealthCheckPeriod = 1 * time.Minute

	// Create pool
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return fmt.Errorf("create pool: %w", err)
	}

	Pool = pool
	return nil
}

func Close() {
	if Pool != nil {
		Pool.Close()
	}
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}
