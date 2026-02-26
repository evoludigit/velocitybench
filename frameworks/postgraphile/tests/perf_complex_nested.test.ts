import request from 'supertest';
import { Pool } from 'pg';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { performance } from 'perf_hooks';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * Complex Nested Query Performance Benchmarks - PostGraphile
 *
 * Tests performance of deeply nested GraphQL queries with multiple levels.
 */
describe('Complex Nested Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:nested'] }, () => {
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

  it('should handle 3+ level deep nesting efficiently', async () => {
    // Arrange - User -> Posts -> Comments -> Author
    const users = await Promise.all(
      Array.from({ length: 5 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      const posts = await Promise.all(
        Array.from({ length: 3 }, (_, i) =>
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

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 5) {
              nodes {
                id
                fullName
                postsByFkAuthor {
                  nodes {
                    id
                    title
                    commentsByFkPost {
                      nodes {
                        id
                        content
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
    expect(avgTime).toBeLessThan(80);
  });

  it('should measure field selection impact on nested queries', async () => {
    // Arrange
    const user = await factory.createUser({ name: 'Author' });
    await Promise.all(
      Array.from({ length: 10 }, (_, i) =>
        factory.createPost({ fk_author: user.pk_user, title: `Post ${i}`, content: `Content ${i}` })
      )
    );
    const iterations = 30;
    const fullTimings: number[] = [];
    const sparseTimings: number[] = [];

    // Act - Full fields
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id fullName email bio username createdAt updatedAt
              postsByFkAuthor {
                nodes { id title content published createdAt updatedAt }
              }
            }
          }`,
        });
      const duration = performance.now() - start;
      fullTimings.push(duration);
      expect(response.status).toBe(200);
    }

    // Act - Sparse fields
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id fullName
              postsByFkAuthor { nodes { id title } }
            }
          }`,
        });
      const duration = performance.now() - start;
      sparseTimings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const fullAvg = fullTimings.reduce((a, b) => a + b, 0) / fullTimings.length;
    const sparseAvg = sparseTimings.reduce((a, b) => a + b, 0) / sparseTimings.length;

    console.log(`Field selection - Full: ${fullAvg.toFixed(3)}ms, Sparse: ${sparseAvg.toFixed(3)}ms`);
    expect(fullAvg).toBeLessThan(40);
    expect(sparseAvg).toBeLessThan(35);
  });

  it('should handle nested list performance efficiently', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 10 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await Promise.all(
        Array.from({ length: 5 }, (_, i) =>
          factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
        )
      );
    }
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 10) {
              nodes {
                id
                fullName
                postsByFkAuthor { nodes { id title } }
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
    console.log(`Nested lists (10 users, 5 posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });

  it('should measure large nested result set performance', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 20 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await Promise.all(
        Array.from({ length: 10 }, (_, i) =>
          factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
        )
      );
    }
    const iterations = 15;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 20) {
              nodes {
                id
                fullName
                postsByFkAuthor { nodes { id title } }
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
    console.log(`Large nested (20 users, 10 posts, 200 total) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(80);
  });

  it('should handle deep nesting stress test', async () => {
    // Arrange - 4 levels
    const users = await Promise.all(
      Array.from({ length: 3 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      const posts = await Promise.all(
        Array.from({ length: 4 }, (_, i) =>
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
    }
    const iterations = 15;
    const timings: number[] = [];

    // Act
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
                        userByFkAuthor {
                          id
                          postsByFkAuthor { nodes { id } }
                        }
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
    const maxTime = Math.max(...timings);
    console.log(`Deep nesting stress (4 levels) - Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(100);
  });

  it('should measure pagination impact on nested queries', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 20 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await Promise.all(
        Array.from({ length: 20 }, (_, i) =>
          factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
        )
      );
    }
    const iterations = 15;
    const timings: number[] = [];
    const pageSize = 5;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 10) {
              nodes {
                id
                postsByFkAuthor(first: ${pageSize}) { nodes { id title } }
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
    console.log(`Nested with pagination (10 users, ${pageSize} posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });

  it('should measure nested filtering performance', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 15 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await Promise.all(
        Array.from({ length: 10 }, (_, i) =>
          factory.createPost({
            fk_author: user.pk_user,
            title: `Post ${i}`,
            published: i % 2 === 0,
          })
        )
      );
    }
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 15) {
              nodes {
                id
                postsByFkAuthor(condition: { published: true }) {
                  nodes { id title }
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
    console.log(`Nested filtering (15 users) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(70);
  });
}, 120000);
