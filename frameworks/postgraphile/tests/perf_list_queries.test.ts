import request from 'supertest';
import { Pool } from 'pg';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { performance } from 'perf_hooks';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * List Query Performance Benchmarks - PostGraphile
 *
 * Tests list operations with pagination, sorting, and large datasets via GraphQL.
 */
describe('List Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:list'] }, () => {
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

  it('should list users with pagination efficiently', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 50 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
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
          query: `{ allUsers(first: ${pageSize}) { nodes { id fullName } } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
      expect(response.body.data.allUsers.nodes.length).toBeLessThanOrEqual(pageSize);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`List users (pagination ${pageSize}) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should list posts with limit efficiently', async () => {
    // Arrange
    const user = await factory.createUser();
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        factory.createPost({ fk_author: user.pk_user, title: `Post ${i}` })
      )
    );
    const iterations = 30;
    const timings: number[] = [];
    const limit = 20;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allPosts(first: ${limit}) { nodes { id title } } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`List posts (limit ${limit}) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should handle large list performance (100+ items)', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 150 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
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
          query: `{ allUsers(first: 100) { nodes { id fullName } } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Large list (100 users) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(60);
  });

  it('should measure cursor-based pagination performance', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
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
          query: `{ allUsers(first: ${pageSize}) {
            nodes { id fullName }
            pageInfo { hasNextPage endCursor }
          } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Cursor pagination - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should measure sorting performance', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
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
          query: `{ allUsers(first: 50, orderBy: FULL_NAME_ASC) { nodes { id fullName } } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Sorting (100 items) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(40);
  });

  it('should measure combined filters with pagination', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
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
          query: `{ allUsers(first: ${pageSize}, condition: { username: "user1" }) { nodes { id fullName } } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filtered pagination - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should measure count query performance', async () => {
    // Arrange
    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        factory.createUser({ name: `User ${i}` })
      )
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers { totalCount } }`,
        });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(response.status).toBe(200);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Count query - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(20);
  });
}, 120000);
