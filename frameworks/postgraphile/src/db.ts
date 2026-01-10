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

    // Test connection
    await client.query('SELECT NOW()');

    // Apply PostGraphile-specific smart tags
    // These configure which columns are exposed in the GraphQL schema
    await applyPostGraphileSchema(client);

    client.release();
    console.log('✓ Database connected successfully');
    console.log('✓ PostGraphile smart tags applied');
    return true;
  } catch (err) {
    console.error('✗ Database connection failed:', err);
    return false;
  }
}

async function applyPostGraphileSchema(client: any) {
  // Apply PostGraphile smart tags to control GraphQL schema generation
  // These comments are parsed by PostGraphile during schema introspection

  const smartTags = `
    -- tb_user table smart tags
    COMMENT ON COLUMN benchmark.tb_user.pk_user IS E'@omit all\\nInternal primary key for database performance.';
    COMMENT ON COLUMN benchmark.tb_user.created_at IS E'@omit create,update\\nTimestamp when user was created (read-only, server-managed).';
    COMMENT ON COLUMN benchmark.tb_user.updated_at IS E'@omit create,update\\nTimestamp when user was last updated (read-only, server-managed).';

    -- tb_post table smart tags
    COMMENT ON COLUMN benchmark.tb_post.pk_post IS E'@omit all\\nInternal primary key for database performance.';
    COMMENT ON COLUMN benchmark.tb_post.fk_author IS E'@omit all\\nInternal foreign key - use "author" relation instead.';
    COMMENT ON COLUMN benchmark.tb_post.created_at IS E'@omit create,update\\nTimestamp when post was created (read-only, server-managed).';
    COMMENT ON COLUMN benchmark.tb_post.updated_at IS E'@omit create,update\\nTimestamp when post was last updated (read-only, server-managed).';

    -- tb_comment table smart tags
    COMMENT ON COLUMN benchmark.tb_comment.pk_comment IS E'@omit all\\nInternal primary key for database performance.';
    COMMENT ON COLUMN benchmark.tb_comment.fk_post IS E'@omit all\\nInternal foreign key - use "post" relation instead.';
    COMMENT ON COLUMN benchmark.tb_comment.fk_author IS E'@omit all\\nInternal foreign key - use "author" relation instead.';
    COMMENT ON COLUMN benchmark.tb_comment.fk_parent IS E'@omit all\\nInternal foreign key - use "parentComment" relation instead.';
    COMMENT ON COLUMN benchmark.tb_comment.created_at IS E'@omit create,update\\nTimestamp when comment was created (read-only, server-managed).';
    COMMENT ON COLUMN benchmark.tb_comment.updated_at IS E'@omit create,update\\nTimestamp when comment was last updated (read-only, server-managed).';
  `;

  try {
    await client.query(smartTags);
  } catch (err) {
    // Smart tags may already exist, which is fine
    console.debug('Note: Smart tags may have already been applied:', err instanceof Error ? err.message : err);
  }
}

export function getPool() {
  return pool;
}

export async function closeDatabase() {
  await pool.end();
}
