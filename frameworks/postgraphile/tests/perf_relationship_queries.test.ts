import request from 'supertest';
import { Pool } from 'pg';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { performance } from 'perf_hooks';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * Relationship Query Performance Benchmarks - PostGraphile
 *
 * Tests performance of queries involving entity relationships via GraphQL nested queries.
 */
describe('Relationship Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:relationships'] }, () => {
  let server: any;
  let pool: Pool;
  let factory: TestFactory;

  beforeAll(async () => {
    server = await startServer();
    pool = new Pool({
      user: process.env.DB_USER || 'benchmark',
      password: process.env.DB_PASSWORD || 'benchmark123',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5434'),
      database: process.env.DB_NAME || 'velocitybench_benchmark',
    });
    factory = new TestFactory(pool);
  });

  afterAll(async () => {
    await pool.end();
    server.close();
  }, 15000);

  beforeEach(async () => {
    await factory.startTransaction();
  });

  afterEach(async () => {
    await factory.cleanup();
  });

  it('should resolve user with posts (1-to-many) efficiently', async () => {
    // Arrange
    const user = await factory.createUser({ name: 'Author' });
    await Promise.all(
      Array.from({ length: 10 }, (_, i) =>
        factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
      )
    );
    const iterations = 30;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id
              fullName
              postsByFkAuthor { nodes { id title } }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
      expect(response.body.data.userById.postsByFkAuthor.nodes.length).toBe(10);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`User with posts (10 posts) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(25);
  });

  it('should resolve posts with comments (1-to-many) efficiently', async () => {
    // Arrange
    const user = await factory.createUser();
    const post = await factory.createPost({ fk_author: user.pk_user });
    await Promise.all(
      Array.from({ length: 20 }, (_, i) =>
        factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user, content: `Comment ${i}` })
      )
    );
    const iterations = 30;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            postById(id: "${post.id}") {
              id
              title
              commentsByFkPost { nodes { id content } }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Post with comments (20 comments) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should resolve comments with author (many-to-1) efficiently', async () => {
    // Arrange
    const user = await factory.createUser({ name: 'Author' });
    const post = await factory.createPost({ fk_author: user.pk_user });
    const comment = await factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user });
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            commentById(id: "${comment.id}") {
              id
              content
              userByFkAuthor { id fullName }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Comment with author - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(20);
  });

  it('should measure 2-level nesting performance', async () => {
    // Arrange
    const user = await factory.createUser();
    const posts = await Promise.all(
      Array.from({ length: 5 }, (_, i) =>
        factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
      )
    );
    for (const post of posts) {
      await Promise.all(
        Array.from({ length: 3 }, (_, i) =>
          factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user })
        )
      );
    }
    const iterations = 30;
    const timings: number[] = [];

    // Act - User -> Posts -> Comments
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id
              postsByFkAuthor {
                nodes {
                  id
                  title
                  commentsByFkPost { nodes { id content } }
                }
              }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`2-level nesting (User->Posts->Comments) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(40);
  });

  it('should measure 3-level nesting performance', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 3 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      const posts = await Promise.all(
        Array.from({ length: 2 }, (_, i) =>
          factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
        )
      );
      for (const post of posts) {
        await Promise.all(
          Array.from({ length: 2 }, (_, i) =>
            factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user })
          )
        );
      }
    }
    const iterations = 20;
    const timings: number[] = [];

    // Act - Users -> Posts -> Comments -> Author
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 3) {
              nodes {
                id
                postsByFkAuthor {
                  nodes {
                    id
                    commentsByFkPost {
                      nodes {
                        id
                        userByFkAuthor { id fullName }
                      }
                    }
                  }
                }
              }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`3-level nesting - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });

  it('should measure batch loading efficiency', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 10 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await Promise.all(
        Array.from({ length: 5 }, (_, i) =>
          factory.createPost({ fk_author: user.pk_user })
        )
      );
    }
    const iterations = 20;
    const timings: number[] = [];

    // Act - DataLoader should batch these
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 10) {
              nodes {
                id
                postsByFkAuthor { nodes { id } }
              }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Batch loading (10 users, 5 posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });

  it('should handle many relationships efficiently', async () => {
    // Arrange
    const user = await factory.createUser({ name: 'Prolific' });
    await Promise.all(
      Array.from({ length: 50 }, (_, i) =>
        factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
      )
    );
    const iterations = 15;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id
              postsByFkAuthor(first: 50) { nodes { id title } }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Many relationships (50 posts) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });
}, 120000);
