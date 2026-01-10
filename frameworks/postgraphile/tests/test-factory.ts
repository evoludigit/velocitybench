import { Pool, PoolClient } from 'pg';

export class TestFactory {
  private testClient: PoolClient | null = null;

  constructor(private pool: Pool) {}

  /**
   * Start a test transaction for isolation
   * Each test gets its own transaction that can be rolled back
   * This is better than truncating tables - PostGraphile's schema stays intact
   */
  async startTransaction() {
    this.testClient = await this.pool.connect();
    await this.testClient.query('BEGIN ISOLATION LEVEL READ COMMITTED');
  }

  /**
   * Rollback the test transaction
   * All test data is automatically cleaned up, no manual truncation needed
   */
  async rollbackTransaction() {
    if (this.testClient) {
      try {
        await this.testClient.query('ROLLBACK');
      } finally {
        this.testClient.release();
        this.testClient = null;
      }
    }
  }

  /**
   * Get the appropriate client for queries
   * Uses test transaction if one is active, otherwise gets a new connection
   * This ensures test data stays within the transaction scope
   */
  private async getClient(): Promise<{ client: PoolClient; shouldRelease: boolean }> {
    if (this.testClient) {
      return { client: this.testClient, shouldRelease: false };
    }
    return { client: await this.pool.connect(), shouldRelease: true };
  }

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

    const { client, shouldRelease } = await this.getClient();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_user (username, email, first_name, last_name, bio)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [username, email, first_name, last_name, bio]
      );
      return result.rows[0];
    } finally {
      if (shouldRelease) {
        client.release();
      }
    }
  }

  /**
   * Create a test post with author relationship
   * Trinity Pattern: fk_author references tb_user(pk_user)
   */
  async createPost(overrides?: Partial<{
    title: string;
    content: string | null;
    fk_author?: number; // pk_user of the author
    status?: string;
  }>) {
    // Create author if not provided
    let fkAuthor: number;
    if (overrides?.fk_author) {
      fkAuthor = overrides.fk_author;
    } else {
      const user = await this.createUser();
      fkAuthor = user.pk_user;
    }

    const {
      title = `Test Post ${Math.random()}`,
      content = 'Test content',
      status = 'published',
    } = overrides || {};

    const { client, shouldRelease } = await this.getClient();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_post (fk_author, title, content, status)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [fkAuthor, title, content, status]
      );
      return result.rows[0];
    } finally {
      if (shouldRelease) {
        client.release();
      }
    }
  }

  /**
   * Create a test comment
   * Trinity Pattern: References tb_post(pk_post) and tb_user(pk_user)
   */
  async createComment(overrides?: Partial<{
    fk_post?: number;
    fk_author?: number;
    content?: string;
  }>) {
    let fkPost: number;
    let fkAuthor: number;

    if (overrides?.fk_post) {
      fkPost = overrides.fk_post;
    } else {
      const post = await this.createPost();
      fkPost = post.pk_post;
    }

    if (overrides?.fk_author) {
      fkAuthor = overrides.fk_author;
    } else {
      const user = await this.createUser();
      fkAuthor = user.pk_user;
    }

    const content = overrides?.content || 'Test comment';

    const { client, shouldRelease } = await this.getClient();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_comment (fk_post, fk_author, content)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [fkPost, fkAuthor, content]
      );
      return result.rows[0];
    } finally {
      if (shouldRelease) {
        client.release();
      }
    }
  }

  /**
   * Clean up test data via transaction rollback
   * This is called after each test to automatically clean up all test data
   * Much better than truncating tables - respects PostGraphile schema configuration
   */
  async cleanup() {
    await this.rollbackTransaction();
  }
}
