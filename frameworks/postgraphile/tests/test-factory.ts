import { Pool } from 'pg';

export class TestFactory {
  constructor(private pool: Pool) {}

  /**
   * Create a test user
   * Trinity Pattern:
   * - pk_user: integer primary key (internal)
   * - id: UUID (public API identifier)
   * - fk_*: internal foreign keys
   */
  async createUser(overrides?: Partial<{
    name: string;
    email: string;
    bio: string | null;
  }>) {
    const {
      name = `Test User ${Math.random()}`,
      email = `user-${Math.random()}@example.com`,
      bio = 'Test bio',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO users (name, email, bio)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [name, email, bio]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Create a test post with author relationship
   * Trinity Pattern: uses fk_user for internal relationship
   */
  async createPost(overrides?: Partial<{
    title: string;
    content: string;
    fk_user?: number;
    author_id?: number;
  }>) {
    // For backwards compatibility, accept author_id but map to fk_user
    let authorPkUser: number;
    if (overrides?.fk_user) {
      authorPkUser = overrides.fk_user;
    } else if (overrides?.author_id) {
      authorPkUser = overrides.author_id;
    } else {
      const user = await this.createUser();
      authorPkUser = user.pk_user;
    }

    const {
      title = `Test Post ${Math.random()}`,
      content = 'Test content',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO posts (title, content, fk_user)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [title, content, authorPkUser]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Clean up all test data
   */
  async cleanup() {
    const client = await this.pool.connect();
    try {
      // Truncate in correct order (respecting foreign keys)
      await client.query('TRUNCATE TABLE comments CASCADE');
      await client.query('TRUNCATE TABLE posts CASCADE');
      await client.query('TRUNCATE TABLE users CASCADE');
    } finally {
      client.release();
    }
  }
}
