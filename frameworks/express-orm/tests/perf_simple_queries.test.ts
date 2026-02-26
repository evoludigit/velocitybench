import { describe, it, expect, beforeEach } from 'vitest';
import { performance } from 'perf_hooks';
import { TestFactory } from './test-factory';

/**
 * Simple Query Performance Benchmarks
 *
 * Tests basic single-entity query performance with timing measurements.
 * Baseline expectations: <10ms average for simple queries.
 */
describe('Simple Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:simple'] }, () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
    factory.reset();
  });

  it('should get user by ID quickly', () => {
    // Arrange
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice Smith');
    const iterations = 100;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getUser(user.id);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result).toBeDefined();
      expect(result?.id).toBe(user.id);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const maxTime = Math.max(...timings);
    const minTime = Math.min(...timings);

    console.log(`Get user by ID - Min: ${minTime.toFixed(3)}ms, Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
  });

  it('should get post by ID quickly', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const post = factory.createTestPost(user.id, 'Test Post', 'Content');
    const iterations = 100;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getPost(post.id);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result).toBeDefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const maxTime = Math.max(...timings);
    const minTime = Math.min(...timings);

    console.log(`Get post by ID - Min: ${minTime.toFixed(3)}ms, Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
  });

  it('should get comment by ID quickly', () => {
    // Arrange
    const author = factory.createTestUser('author', 'author@example.com', 'Author');
    const post = factory.createTestPost(author.id, 'Post');
    const comment = factory.createTestComment(author.id, post.id, 'Great!');
    const iterations = 100;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getComment(comment.id);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result).toBeDefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const maxTime = Math.max(...timings);
    const minTime = Math.min(...timings);

    console.log(`Get comment by ID - Min: ${minTime.toFixed(3)}ms, Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
  });

  it('should handle empty result quickly', () => {
    // Arrange
    const nonExistentId = 'non-existent-id';
    const iterations = 100;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getUser(nonExistentId);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result).toBeUndefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Empty result query - Min: ${Math.min(...timings).toFixed(3)}ms, Avg: ${avgTime.toFixed(3)}ms, Max: ${Math.max(...timings).toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
  });

  it('should handle null/not found case efficiently', () => {
    // Arrange
    const iterations = 100;
    const timings: number[] = [];
    const randomIds = Array.from({ length: 10 }, () => `random-${Math.random()}`);

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getPost(randomIds[i % 10]);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result).toBeUndefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Not found query - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
  });

  it('should measure field selection impact', () => {
    // Arrange
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Bio text here');
    const iterations = 100;
    const fullTimings: number[] = [];
    const partialTimings: number[] = [];

    // Act - Full object retrieval
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getUser(user.id);
      const duration = performance.now() - start;
      fullTimings.push(duration);
      expect(result).toBeDefined();
    }

    // Act - Partial field access (simulated)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getUser(user.id);
      const id = result?.id;
      const duration = performance.now() - start;
      partialTimings.push(duration);
      expect(id).toBeDefined();
    }

    // Assert
    const fullAvg = fullTimings.reduce((a, b) => a + b, 0) / fullTimings.length;
    const partialAvg = partialTimings.reduce((a, b) => a + b, 0) / partialTimings.length;

    console.log(`Field selection - Full: ${fullAvg.toFixed(3)}ms, Partial: ${partialAvg.toFixed(3)}ms`);
    expect(fullAvg).toBeLessThan(10);
    expect(partialAvg).toBeLessThan(10);
  });

  it('should handle multiple sequential queries efficiently', () => {
    // Arrange
    const users = Array.from({ length: 10 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      for (const user of users) {
        const result = factory.getUser(user.id);
        expect(result).toBeDefined();
      }
      const duration = performance.now() - start;
      timings.push(duration);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const avgPerQuery = avgTime / users.length;

    console.log(`Sequential queries (10 users) - Total: ${avgTime.toFixed(3)}ms, Per query: ${avgPerQuery.toFixed(3)}ms`);
    expect(avgPerQuery).toBeLessThan(10);
  });

  it('should measure concurrent query performance', () => {
    // Arrange
    const users = Array.from({ length: 20 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act - Simulate concurrent access
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const results = users.map(u => factory.getUser(u.id));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(results.every(r => r !== undefined)).toBe(true);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const avgPerQuery = avgTime / users.length;

    console.log(`Concurrent queries (20 users) - Total: ${avgTime.toFixed(3)}ms, Per query: ${avgPerQuery.toFixed(3)}ms`);
    expect(avgPerQuery).toBeLessThan(10);
  });

  it('should measure query performance under load', () => {
    // Arrange - Create dataset
    const users = Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 100;
    const timings: number[] = [];

    // Act - Random access pattern
    for (let i = 0; i < iterations; i++) {
      const randomUser = users[Math.floor(Math.random() * users.length)];
      const start = performance.now();
      const result = factory.getUser(randomUser.id);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result).toBeDefined();
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const p50 = timings.sort((a, b) => a - b)[Math.floor(timings.length * 0.5)];
    const p95 = timings[Math.floor(timings.length * 0.95)];
    const p99 = timings[Math.floor(timings.length * 0.99)];

    console.log(`Query under load (100 users) - Avg: ${avgTime.toFixed(3)}ms, P50: ${p50.toFixed(3)}ms, P95: ${p95.toFixed(3)}ms, P99: ${p99.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
    expect(p95).toBeLessThan(20);
  });
});
