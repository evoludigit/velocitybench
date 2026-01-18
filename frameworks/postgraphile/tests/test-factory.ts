import { Pool, PoolClient } from 'pg';

export class TestFactory {
  private testClient: PoolClient | null = null;

  constructor(private pool: Pool) {}

  /**
   * Start a test transaction for isolation
   * Each test gets its own transaction that can be rolled back
   */
  async startTransaction() {
    this.testClient = await this.pool.connect();
    await this.testClient.query('BEGIN ISOLATION LEVEL READ COMMITTED');
  }

  /**
   * Rollback the test transaction
   * All test data is automatically cleaned up
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
   */
  private async getClient(): Promise<{ client: PoolClient; shouldRelease: boolean }> {
    if (this.testClient) {
      return { client: this.testClient, shouldRelease: false };
    }
    return { client: await this.pool.connect(), shouldRelease: true };
  }

  /**
   * Create a test user
   * Trinity Pattern: tb_user with pk_user (integer PK) + id (UUID)
   */
  async createUser(overrides?: Partial<{
    name: string;        // Maps to first_name for simplicity
    email: string;
    username: string;
    bio: string | null;
  }>) {
    const {
      name = 'Test',
      email = `user-${Math.random().toString(36).substring(7)}@example.com`,
      username = `user_${Math.random().toString(36).substring(7)}`,
      bio = 'Test bio',
    } = overrides || {};

    const { client, shouldRelease } = await this.getClient();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_user (username, email, first_name, last_name, bio)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [username, email, name, 'User', bio]
      );
      return result.rows[0];
    } finally {
      if (shouldRelease) {
        client.release();
      }
    }
  }

  /**
   * Create a test post
   * Trinity Pattern: tb_post with pk_post (integer PK) + id (UUID) + fk_author (FK to tb_user.pk_user)
   */
  async createPost(overrides?: Partial<{
    title: string;
    content: string | null;
    fk_author?: number;
    status?: string;
  }>) {
    let fkAuthor: number;
    if (overrides?.fk_author) {
      fkAuthor = overrides.fk_author;
    } else {
      const user = await this.createUser();
      fkAuthor = user.pk_user;
    }

    const {
      title = `Test Post ${Math.random().toString(36).substring(7)}`,
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
   * Trinity Pattern: tb_comment with pk_comment (integer PK) + id (UUID) + fk_post/fk_author (FKs)
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
   */
  async cleanup() {
    await this.rollbackTransaction();
  }
}
