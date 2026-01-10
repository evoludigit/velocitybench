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
   * Trinity Pattern: fk_user references tb_user(pk_user)
   */
  async createPost(overrides?: Partial<{
    title: string;
    content: string;
    fk_user?: number; // pk_user of the author
    status?: string;
  }>) {
    // Create author if not provided
    let fkUser: number;
    if (overrides?.fk_user) {
      fkUser = overrides.fk_user;
    } else {
      const user = await this.createUser();
      fkUser = user.pk_user;
    }

    const {
      title = `Test Post ${Math.random()}`,
      content = 'Test content',
      status = 'published',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_post (fk_user, title, content, status)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [fkUser, title, content, status]
      );
      return result.rows[0];
    } finally {
      client.release();
    }
  }

  /**
   * Create a test comment
   * Trinity Pattern: References tb_post(pk_post) and tb_user(pk_user)
   */
  async createComment(overrides?: Partial<{
    fk_post?: number;
    fk_user?: number;
    content?: string;
  }>) {
    let fkPost: number;
    let fkUser: number;

    if (overrides?.fk_post) {
      fkPost = overrides.fk_post;
    } else {
      const post = await this.createPost();
      fkPost = post.pk_post;
    }

    if (overrides?.fk_user) {
      fkUser = overrides.fk_user;
    } else {
      const user = await this.createUser();
      fkUser = user.pk_user;
    }

    const content = overrides?.content || 'Test comment';

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_comment (fk_post, fk_user, content)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [fkPost, fkUser, content]
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
