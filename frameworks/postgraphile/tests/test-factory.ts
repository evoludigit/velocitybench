import { Pool } from 'pg';

export class TestFactory {
  constructor(private pool: Pool) {}

  /**
   * Create a test user using the benchmark schema
   * Trinity Pattern:
   * - id: UUID (public API identifier, also primary key)
   * - username: unique identifier
   * - email: contact info
   * - first_name, last_name: personal info
   * - bio: user bio
   */
  async createUser(overrides?: Partial<{
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    bio: string | null;
  }>) {
    const {
      username = `user_${Math.random().toString(36).substring(7)}`,
      email = `user-${Math.random()}@example.com`,
      first_name = 'Test',
      last_name = 'User',
      bio = 'Test bio',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_user (username, email, first_name, last_name, bio)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [username, email, first_name, last_name, bio]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Create a test post with author relationship
   * Trinity Pattern: author_id references tb_user(id)
   */
  async createPost(overrides?: Partial<{
    title: string;
    content: string;
    author_id?: string; // UUID of the author
    status?: string;
  }>) {
    // Create author if not provided
    let authorId: string;
    if (overrides?.author_id) {
      authorId = overrides.author_id;
    } else {
      const user = await this.createUser();
      authorId = user.id;
    }

    const {
      title = `Test Post ${Math.random()}`,
      content = 'Test content',
      status = 'published',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_post (author_id, title, content, status)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [authorId, title, content, status]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Create a test comment
   * Trinity Pattern: References tb_post(id) and tb_user(id)
   */
  async createComment(overrides?: Partial<{
    post_id?: string;
    author_id?: string;
    content?: string;
  }>) {
    let postId: string;
    let authorId: string;

    if (overrides?.post_id) {
      postId = overrides.post_id;
    } else {
      const post = await this.createPost();
      postId = post.id;
    }

    if (overrides?.author_id) {
      authorId = overrides.author_id;
    } else {
      const user = await this.createUser();
      authorId = user.id;
    }

    const content = overrides?.content || 'Test comment';

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_comment (post_id, author_id, content)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [postId, authorId, content]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Clean up all test data (respecting foreign key order)
   */
  async cleanup() {
    const client = await this.pool.connect();
    try {
      // Truncate in correct order (respecting foreign keys)
      await client.query('TRUNCATE TABLE benchmark.tv_user CASCADE');
      await client.query('TRUNCATE TABLE benchmark.tv_post CASCADE');
      await client.query('TRUNCATE TABLE benchmark.tb_comment CASCADE');
      await client.query('TRUNCATE TABLE benchmark.tb_post CASCADE');
      await client.query('TRUNCATE TABLE benchmark.tb_user CASCADE');
    } finally {
      client.release();
    }
  }
}
