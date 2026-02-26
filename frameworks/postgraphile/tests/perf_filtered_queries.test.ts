import request from 'supertest';
import { Pool } from 'pg';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { performance } from 'perf_hooks';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * Filtered Query Performance Benchmarks - PostGraphile
 *
 * Tests query performance with various filtering conditions via GraphQL.
 */
describe('Filtered Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:filtered'] }, () => {
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

  it('should filter users by name efficiently', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        factory.createUser({ name: `User ${i}`, username: `user${i}` })
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
            allUsers(condition: { username: "user1" }) {
              nodes { id fullName username }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter by name - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should filter posts by title efficiently', async () => {
    // Arrange
    const user = await factory.createUser();
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
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
            allPosts(condition: { title: "Post 1" }) {
              nodes { id title }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter by title - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should handle filter with pagination efficiently', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 200 }, (_, i) =>
        factory.createUser({ name: `User ${i}`, username: `user${i}` })
      )
    );
    const iterations = 30;
    const timings: number[] = [];
    const pageSize = 10;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: ${pageSize}, filter: { fullName: { includesInsensitive: "User 1" } }) {
              nodes { id fullName }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter with pagination - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(45);
  });

  it('should measure complex filter performance', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 150 }, (_, i) =>
        factory.createUser({
          name: `User ${i}`,
          username: `user${i}`,
          bio: i % 3 === 0 ? 'Active user' : null,
        })
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
            allUsers(filter: {
              and: [
                { bio: { isNull: false } }
                { fullName: { includesInsensitive: "User 1" } }
              ]
            }) {
              nodes { id fullName bio }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Complex filter - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });

  it('should measure filter performance on large dataset', async () => {
    // Arrange
    const userCount = 500;
    await Promise.all(
      Array.from({ length: userCount }, (_, i) =>
        factory.createUser({ name: `User ${i}`, username: `user${i}` })
      )
    );
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(filter: { username: { includesInsensitive: "user99" } }) {
              nodes { id username }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const p95 = timings.sort((a, b) => a - b)[Math.floor(timings.length * 0.95)];

    console.log(`Filter large dataset (${userCount} users) - Avg: ${avgTime.toFixed(3)}ms, P95: ${p95.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(80);
  });

  it('should measure sorting with filter performance', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        factory.createUser({ name: `User ${i}`, username: `user${i}` })
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
            allUsers(
              first: 50
              filter: { fullName: { includesInsensitive: "User" } }
              orderBy: FULL_NAME_ASC
            ) {
              nodes { id fullName }
            }
          }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter + sort - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });
}, 120000);
