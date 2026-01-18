import { Pool, PoolClient } from 'pg';

export class TestFactory {
  private createdUsers: number[] = [];
  private createdPosts: number[] = [];
  private createdComments: number[] = [];

  constructor(private pool: Pool) {}

  /**
   * Start a test - no-op for PostGraphile since we need committed data
   * PostGraphile uses a separate connection pool, so transactions won't be visible
   */
  async startTransaction() {
    // No-op: PostGraphile requires committed data
    // We'll track created IDs and delete them in cleanup instead
  }

  /**
   * Clean up test data by deleting created records
   * Order matters: comments -> posts -> users (due to FK constraints)
   */
  async cleanup() {
    const client = await this.pool.connect();
    try {
      // Delete in reverse order of dependencies
      if (this.createdComments.length > 0) {
        await client.query(
          `DELETE FROM benchmark.tb_comment WHERE pk_comment = ANY($1)`,
          [this.createdComments]
        );
      }
      if (this.createdPosts.length > 0) {
        await client.query(
          `DELETE FROM benchmark.tb_post WHERE pk_post = ANY($1)`,
          [this.createdPosts]
        );
      }
      if (this.createdUsers.length > 0) {
        await client.query(
          `DELETE FROM benchmark.tb_user WHERE pk_user = ANY($1)`,
          [this.createdUsers]
        );
      }
    } finally {
      client.release();
      // Reset tracking arrays
      this.createdComments = [];
      this.createdPosts = [];
      this.createdUsers = [];
    }
  }

  /**
   * Create a test user
   * Trinity Pattern: tb_user with pk_user (integer PK) + id (UUID)
   */
  async createUser(overrides?: Partial<{
    name: string;        // Maps to full_name
    email: string;
    username: string;
    bio: string | null;
  }>) {
    const randomSuffix = Math.random().toString(36).substring(7);
    const {
      name = 'Test User',
      email = `user-${randomSuffix}@example.com`,
      username = `user_${randomSuffix}`,
      bio = 'Test bio',
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_user (username, identifier, email, full_name, bio)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [username, `user-${randomSuffix}`, email, name, bio]
      );
      const user = result.rows[0];
      this.createdUsers.push(user.pk_user);
      return user;
    } finally {
      client.release();
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
    published?: boolean;
  }>) {
    let fkAuthor: number;
    if (overrides?.fk_author) {
      fkAuthor = overrides.fk_author;
    } else {
      const user = await this.createUser();
      fkAuthor = user.pk_user;
    }

    const randomSuffix = Math.random().toString(36).substring(7);
    const {
      title = `Test Post ${randomSuffix}`,
      content = 'Test content',
      published = true,
    } = overrides || {};

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_post (fk_author, identifier, title, content, published)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [fkAuthor, `post-${randomSuffix}`, title, content, published]
      );
      const post = result.rows[0];
      this.createdPosts.push(post.pk_post);
      return post;
    } finally {
      client.release();
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

    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `INSERT INTO benchmark.tb_comment (fk_post, fk_author, content)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [fkPost, fkAuthor, content]
      );
      const comment = result.rows[0];
      this.createdComments.push(comment.pk_comment);
      return comment;
    } finally {
      client.release();
    }
  }
}
