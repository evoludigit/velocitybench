import { Pool } from 'pg';

const pool = new Pool({
  user: process.env.DB_USER || 'velocitybench',
  password: process.env.DB_PASSWORD || 'password',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'velocitybench_test',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

export async function connectDatabase() {
  try {
    const client = await pool.connect();
    await client.query('SELECT NOW()');
    client.release();
    console.log('✓ Database connected successfully');
    return true;
  } catch (err) {
    console.error('✗ Database connection failed:', err);
    return false;
  }
}

export function getPool() {
  return pool;
}

export async function closeDatabase() {
  await pool.end();
}
