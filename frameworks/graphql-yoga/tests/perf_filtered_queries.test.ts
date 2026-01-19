import { describe, it, expect, beforeEach } from 'vitest';
import { performance } from 'perf_hooks';
import { TestFactory } from './test-factory';

/**
 * Filtered Query Performance Benchmarks
 *
 * Tests query performance with various filtering conditions.
 * Measures impact of filters, search, and complex conditions.
 */
describe('Filtered Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:filtered'] }, () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
    factory.reset();
  });

  it('should filter users by name efficiently', () => {
    // Arrange
    Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const searchTerm = 'user1';

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u => u.username.includes(searchTerm));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter by name - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(25);
  });

  it('should filter posts by date range efficiently', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const now = new Date();
    Array.from({ length: 100 }, (_, i) => {
      const post = factory.createTestPost(user.id, `Post ${i}`);
      post.created_at = new Date(now.getTime() - i * 60000); // Each post 1 minute earlier
      return post;
    });
    const iterations = 50;
    const timings: number[] = [];
    const rangeStart = new Date(now.getTime() - 30 * 60000); // Last 30 minutes

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allPosts = factory.getAllPosts();
      const filtered = allPosts.filter(p => p.created_at >= rangeStart);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter by date range - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should filter comments by content efficiently', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const post = factory.createTestPost(user.id, 'Post');
    Array.from({ length: 100 }, (_, i) =>
      factory.createTestComment(user.id, post.id, `Comment ${i % 2 === 0 ? 'awesome' : 'good'} ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const searchTerm = 'awesome';

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allComments = factory.getAllComments();
      const filtered = allComments.filter(c => c.content.includes(searchTerm));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter by content - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should handle multiple filter conditions efficiently', () => {
    // Arrange
    Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`, i % 2 === 0 ? 'Bio text' : undefined)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u =>
        u.username.includes('user') &&
        u.full_name.includes('User') &&
        u.bio !== null
      );
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Multiple filter conditions - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should measure filter with pagination performance', () => {
    // Arrange
    Array.from({ length: 200 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];
    const pageSize = 10;
    const searchTerm = 'user1';

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u => u.username.includes(searchTerm));
      const paginated = filtered.slice(0, pageSize);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(paginated.length).toBeLessThanOrEqual(pageSize);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Filter with pagination - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should compare case-sensitive vs case-insensitive search', () => {
    // Arrange
    Array.from({ length: 100 }, (_, i) =>
      factory.createTestUser(`User${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 50;
    const sensitiveTimings: number[] = [];
    const insensitiveTimings: number[] = [];
    const searchTerm = 'user';

    // Act - Case sensitive
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u => u.username.includes(searchTerm));
      const duration = performance.now() - start;
      sensitiveTimings.push(duration);
    }

    // Act - Case insensitive
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u => u.username.toLowerCase().includes(searchTerm.toLowerCase()));
      const duration = performance.now() - start;
      insensitiveTimings.push(duration);
    }

    // Assert
    const sensitiveAvg = sensitiveTimings.reduce((a, b) => a + b, 0) / sensitiveTimings.length;
    const insensitiveAvg = insensitiveTimings.reduce((a, b) => a + b, 0) / insensitiveTimings.length;

    console.log(`Case-sensitive: ${sensitiveAvg.toFixed(3)}ms, Case-insensitive: ${insensitiveAvg.toFixed(3)}ms`);
    expect(sensitiveAvg).toBeLessThan(30);
    expect(insensitiveAvg).toBeLessThan(35);
  });

  it('should measure index usage performance (simulated)', () => {
    // Arrange
    Array.from({ length: 500 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 30;
    const indexedTimings: number[] = [];
    const scanTimings: number[] = [];

    // Act - Indexed lookup (by ID - Map lookup)
    const users = factory.getAllUsers();
    const targetUser = users[250];
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const result = factory.getUser(targetUser.id);
      const duration = performance.now() - start;
      indexedTimings.push(duration);
      expect(result).toBeDefined();
    }

    // Act - Full scan (by name)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const result = allUsers.find(u => u.username === targetUser.username);
      const duration = performance.now() - start;
      scanTimings.push(duration);
      expect(result).toBeDefined();
    }

    // Assert
    const indexedAvg = indexedTimings.reduce((a, b) => a + b, 0) / indexedTimings.length;
    const scanAvg = scanTimings.reduce((a, b) => a + b, 0) / scanTimings.length;

    console.log(`Indexed: ${indexedAvg.toFixed(3)}ms, Full scan: ${scanAvg.toFixed(3)}ms`);
    expect(indexedAvg).toBeLessThan(scanAvg);
  });

  it('should measure full-text search performance', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    Array.from({ length: 200 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`, `This is content with keywords like performance, benchmark, testing ${i}`)
    );
    const iterations = 30;
    const timings: number[] = [];
    const keywords = ['performance', 'benchmark', 'testing'];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allPosts = factory.getAllPosts();
      const filtered = allPosts.filter(p =>
        keywords.some(keyword => p.content.toLowerCase().includes(keyword))
      );
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Full-text search (3 keywords, 200 posts) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });

  it('should measure complex filter expression performance', () => {
    // Arrange
    Array.from({ length: 150 }, (_, i) =>
      factory.createTestUser(
        `user${i}`,
        `user${i}@example.com`,
        `User ${i}`,
        i % 3 === 0 ? 'Active user' : undefined
      )
    );
    const iterations = 30;
    const timings: number[] = [];

    // Act - Complex filter with multiple conditions
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u =>
        (u.username.startsWith('user1') || u.username.startsWith('user2')) &&
        u.bio !== null &&
        u.full_name.includes('User')
      );
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Complex filter expression - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(40);
  });

  it('should measure filter performance on large dataset', () => {
    // Arrange
    const userCount = 1000;
    Array.from({ length: userCount }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    const iterations = 20;
    const timings: number[] = [];
    const searchTerm = 'user99';

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.filter(u => u.username.includes(searchTerm));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBeGreaterThan(0);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const p95 = timings.sort((a, b) => a - b)[Math.floor(timings.length * 0.95)];

    console.log(`Filter on large dataset (${userCount} users) - Avg: ${avgTime.toFixed(3)}ms, P95: ${p95.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(100);
  });
});
