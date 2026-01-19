import request from 'supertest';
import { Pool } from 'pg';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { performance } from 'perf_hooks';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * Simple Query Performance Benchmarks - PostGraphile
 *
 * Tests basic single-entity GraphQL query performance with timing measurements.
 * Baseline expectations: <15ms average for simple queries (includes HTTP overhead).
 */
describe('Simple Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:simple'] }, () => {
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

  it('should get user by ID quickly', async () => {
    // Arrange
    const user = await factory.createUser({ name: 'Alice', email: 'alice@example.com' });
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id fullName email } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeDefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const maxTime = Math.max(...timings);
    const minTime = Math.min(...timings);

    console.log(`Get user by ID - Min: ${minTime.toFixed(3)}ms, Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(15);
  });

  it('should get post by ID quickly', async () => {
    // Arrange
    const user = await factory.createUser();
    const post = await factory.createPost({ fk_author: user.pk_user, title: 'Test Post' });
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title content } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
      expect(response.body.data.postById).toBeDefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Get post by ID - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(15);
  });

  it('should get comment by ID quickly', async () => {
    // Arrange
    const user = await factory.createUser();
    const post = await factory.createPost({ fk_author: user.pk_user });
    const comment = await factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user, content: 'Great!' });
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ commentById(id: "${comment.id}") { id content } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
      expect(response.body.data.commentById).toBeDefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Get comment by ID - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(15);
  });

  it('should handle empty result quickly', async () => {
    // Arrange
    const iterations = 50;
    const timings: number[] = [];
    const nonExistentId = '00000000-0000-0000-0000-000000000000';

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${nonExistentId}") { id fullName } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeNull();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Empty result query - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(15);
  });

  it('should measure field selection impact', async () => {
    // Arrange
    const user = await factory.createUser({ name: 'Alice', email: 'alice@example.com', bio: 'Bio text' });
    const iterations = 50;
    const fullTimings: number[] = [];
    const partialTimings: number[] = [];

    // Act - Full field selection
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id fullName email bio username createdAt updatedAt } }`,
        });
      const duration = performance.now() - start;
      fullTimings.push(duration);
      expect(response.status).toBe(200);
    }

    // Act - Partial field selection
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id fullName } }`,
        });
      const duration = performance.now() - start;
      partialTimings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const fullAvg = fullTimings.reduce((a, b) => a + b, 0) / fullTimings.length;
    const partialAvg = partialTimings.reduce((a, b) => a + b, 0) / partialTimings.length;

    console.log(`Field selection - Full: ${fullAvg.toFixed(3)}ms, Partial: ${partialAvg.toFixed(3)}ms`);
    expect(fullAvg).toBeLessThan(20);
    expect(partialAvg).toBeLessThan(15);
  });

  it('should handle multiple sequential queries efficiently', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 10 }, (_, i) =>
        factory.createUser({ name: `User ${i}`, email: `user${i}@example.com` })
      )
    );
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      for (const user of users) {
        const response = await request(server)
          .post('/graphql')
          .send({
            query: `{ userById(id: "${user.id}") { id fullName } }`,
          });
        expect(response.status).toBe(200);
      }
      const duration = performance.now() - start;
      timings.push(duration);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const avgPerQuery = avgTime / users.length;

    console.log(`Sequential queries (10 users) - Total: ${avgTime.toFixed(3)}ms, Per query: ${avgPerQuery.toFixed(3)}ms`);
    expect(avgPerQuery).toBeLessThan(20);
  });

  it('should measure batch query performance', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 5 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act - Batch query using aliases
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const query = users.map((user, idx) =>
        `user${idx}: userById(id: "${user.id}") { id fullName }`
      ).join('\n');
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ ${query} }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const avgPerQuery = avgTime / users.length;

    console.log(`Batch query (5 users) - Total: ${avgTime.toFixed(3)}ms, Per query: ${avgPerQuery.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should measure query performance under load', async () => {
    // Arrange
    const users = await Promise.all(
      Array.from({ length: 50 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act - Random access pattern
    for (let i = 0; i < iterations; i++) {
      const randomUser = users[Math.floor(Math.random() * users.length)];
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${randomUser.id}") { id fullName } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const sorted = timings.sort((a, b) => a - b);
    const p50 = sorted[Math.floor(sorted.length * 0.5)];
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    const p99 = sorted[Math.floor(sorted.length * 0.99)];

    console.log(`Query under load (50 users) - Avg: ${avgTime.toFixed(3)}ms, P50: ${p50.toFixed(3)}ms, P95: ${p95.toFixed(3)}ms, P99: ${p99.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(20);
    expect(p95).toBeLessThan(40);
  });
}, 120000);
