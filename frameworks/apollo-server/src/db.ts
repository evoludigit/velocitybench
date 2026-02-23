import pg from 'pg';

const { Pool } = pg;

export const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'velocitybench_benchmark',
  user: process.env.DB_USER || 'benchmark',
  password: process.env.DB_PASSWORD || 'benchmark123',
  // Connection pool settings
  min: 10,
  max: 50,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
  // Statement caching
  statement_timeout: 30000,
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, closing database pool...');
  await pool.end();
  process.exit(0);
});

export async function query<T = any>(text: string, params?: any[]): Promise<T[]> {
  const result = await pool.query(text, params);
  return result.rows as T[];
}

export async function queryOne<T = any>(text: string, params?: any[]): Promise<T | null> {
  const rows = await query<T>(text, params);
  return rows[0] || null;
}
