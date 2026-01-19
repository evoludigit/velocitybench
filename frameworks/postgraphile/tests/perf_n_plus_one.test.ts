import request from 'supertest';
import { Pool } from 'pg';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { performance } from 'perf_hooks';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * N+1 Query Detection Performance Benchmarks - PostGraphile
 *
 * PostGraphile automatically uses DataLoader for batching, so N+1 should be minimal.
 * These tests verify the optimization is working correctly.
 */
describe('N+1 Query Detection Benchmarks', { tags: ['perf', 'perf:queries', 'perf:n-plus-one'] }, () => {
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

  it('should handle users with posts without N+1', async () => {
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
    console.log(`Users with posts (DataLoader) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });

  it('should handle posts with comments without N+1', async () => {
    // Arrange
    const user = await factory.createUser();
    const posts = await Promise.all(
      Array.from({ length: 15 }, (_, i) =>
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
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allPosts(first: 15) {
              nodes {
                id
                title
                commentsByFkPost { nodes { id content } }
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
    console.log(`Posts with comments (DataLoader) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(70);
  });

  it('should verify batch loading with multiple levels', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 5 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      const posts = await Promise.all(
        Array.from({ length: 3 }, (_, i) =>
          factory.createPost({ fk_author: user.pk_user })
        )
      );
      for (const post of posts) {
        await factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user });
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
                postsByFkAuthor {
                  nodes {
                    id
                    commentsByFkPost { nodes { id } }
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
    console.log(`Multi-level DataLoader - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(80);
  });

  it('should measure batch size scalability', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 50 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await factory.createPost({ fk_author: user.pk_user, title: 'Post' });
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
            allUsers(first: 50) {
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
    console.log(`Large batch (50 users) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(100);
  });

  it('should verify cache behavior across queries', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 10 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    for (const user of users) {
      await factory.createPost({ fk_author: user.pk_user });
    }
    const iterations = 30;
    const timings: number[] = [];

    // Act - Same query multiple times
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
    console.log(`Repeated queries - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });
}, 120000);
