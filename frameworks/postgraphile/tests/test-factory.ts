import { Pool } from 'pg';

export class TestFactory {
  constructor(private pool: Pool) {}

  /**
   * Create a test user
   * Trinity Pattern: id (primary), email (alternative), and relationships via fk
   */
  async createUser(overrides?: Partial<{
    id: number;
    name: string;
    email: string;
    bio: string | null;
  }>) {
    const {
      id = Math.floor(Math.random() * 1000000),
      name = `Test User ${Math.random()}`,
      email = `user-${Math.random()}@example.com`,
      bio = 'Test bio',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO users (id, name, email, bio)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [id, name, email, bio]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Create a test post with author relationship
   */
  async createPost(overrides?: Partial<{
    id: number;
    title: string;
    content: string;
    author_id: number;
  }>) {
    // First create author if not specified
    const authorId = overrides?.author_id || (await this.createUser()).id;

    const {
      id = Math.floor(Math.random() * 1000000),
      title = `Test Post ${Math.random()}`,
      content = 'Test content',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO posts (id, title, content, author_id)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [id, title, content, authorId]
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
      await client.query('TRUNCATE TABLE posts CASCADE');
      await client.query('TRUNCATE TABLE users CASCADE');
    } finally {
      client.release();
    }
  }
}
