import { describe, it, expect, beforeEach } from 'vitest';
import { performance } from 'perf_hooks';
import { TestFactory } from './test-factory';

/**
 * List Query Performance Benchmarks
 *
 * Tests list operations with pagination, sorting, and large datasets.
 * Baseline expectations vary by operation complexity.
 */
describe('List Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:list'] }, () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
    factory.reset();
  });

  it('should list users with pagination efficiently', () => {
    // Arrange
    const userCount = 50;
    Array.from({ length: userCount }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const pageSize = 10;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const page = allUsers.slice(0, pageSize);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(page.length).toBe(pageSize);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`List users (pagination ${pageSize}) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(20);
  });

  it('should list posts with limit efficiently', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    Array.from({ length: 100 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`, `Content ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const limit = 20;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allPosts = factory.getAllPosts();
      const limited = allPosts.slice(0, limit);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(limited.length).toBe(limit);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`List posts (limit ${limit}) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(20);
  });

  it('should list comments with offset efficiently', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const post = factory.createTestPost(user.id, 'Post');
    Array.from({ length: 50 }, (_, i) =>
      factory.createTestComment(user.id, post.id, `Comment ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const offset = 10;
    const limit = 10;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const comments = factory.getCommentsByPost(post.pk_post);
      const paginated = comments.slice(offset, offset + limit);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(paginated.length).toBe(limit);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`List comments (offset ${offset}, limit ${limit}) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(20);
  });

  it('should handle large list performance (100+ items)', () => {
    // Arrange
    const userCount = 150;
    Array.from({ length: userCount }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 30;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const users = factory.getAllUsers();
      const duration = performance.now() - start;
      timings.push(duration);
      expect(users.length).toBe(userCount);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Large list (${userCount} users) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });

  it('should handle very large list performance (1000+ items)', () => {
    // Arrange
    const userCount = 1000;
    Array.from({ length: userCount }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 10;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const users = factory.getAllUsers();
      const duration = performance.now() - start;
      timings.push(duration);
      expect(users.length).toBe(userCount);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Very large list (${userCount} users) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(200);
  });

  it('should measure cursor-based pagination performance', () => {
    // Arrange
    const users = Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const pageSize = 10;

    // Act - Simulate cursor pagination
    for (let i = 0; i < iterations; i++) {
      const cursorIndex = Math.floor(Math.random() * (users.length - pageSize));
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const page = allUsers.slice(cursorIndex, cursorIndex + pageSize);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(page.length).toBe(pageSize);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Cursor pagination - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(25);
  });

  it('should measure sorting performance', () => {
    // Arrange
    const users = Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const sorted = [...allUsers].sort((a, b) => a.username.localeCompare(b.username));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(sorted.length).toBe(users.length);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Sorting (${users.length} items) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should measure combined filters with pagination', () => {
    // Arrange
    const users = Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const pageSize = 10;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u => u.username.includes('user'));
      const paginated = filtered.slice(0, pageSize);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(paginated.length).toBe(pageSize);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filtered pagination - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(25);
  });

  it('should measure count query performance', () => {
    // Arrange
    const userCount = 100;
    Array.from({ length: userCount }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 100;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const count = factory.getUserCount();
      const duration = performance.now() - start;
      timings.push(duration);
      expect(count).toBe(userCount);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Count query - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(5);
  });

  it('should handle empty list efficiently', () => {
    // Arrange
    const iterations = 100;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const users = factory.getAllUsers();
      const duration = performance.now() - start;
      timings.push(duration);
      expect(users.length).toBe(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Empty list query - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(5);
  });
});
