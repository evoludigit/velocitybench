import { describe, it, expect, beforeEach } from 'vitest';
import { performance } from 'perf_hooks';
import { TestFactory } from './test-factory';

/**
 * Complex Nested Query Performance Benchmarks
 *
 * Tests performance of deeply nested queries with multiple levels
 * of relationships and large result sets.
 */
describe('Complex Nested Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:nested'] }, () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
    factory.reset();
  });

  it('should handle 3+ level deep nesting efficiently', () => {
    // Arrange - User -> Posts -> Comments -> Author
    const users = Array.from({ length: 5 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      const posts = Array.from({ length: 3 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
      posts.forEach(post => {
        Array.from({ length: 2 }, (_, i) =>
          factory.createTestComment(user.id, post.id, `Comment ${i}`)
        );
      });
    });
    const iterations = 30;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const result = allUsers.map(user => ({
        user,
        posts: factory.getPostsByAuthor(user.pk_user).map(post => ({
          post,
          comments: factory.getCommentsByPost(post.pk_post).map(comment => ({
            comment,
            author: comment.author,
          })),
        })),
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(result.length).toBe(5);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`3-level nesting (5 users, 3 posts, 2 comments each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });

  it('should measure field selection impact on nested queries', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author', 'Bio text here');
    Array.from({ length: 10 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`, `Content ${i} with more text here`)
    );
    const iterations = 50;
    const fullTimings: number[] = [];
    const sparseTimings: number[] = [];

    // Act - Full field selection
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const posts = factory.getPostsByAuthor(user.pk_user);
      const fullData = {
        ...fetchedUser,
        posts: posts,
      };
      const duration = performance.now() - start;
      fullTimings.push(duration);
      expect(fullData.posts.length).toBe(10);
    }

    // Act - Sparse field selection
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const posts = factory.getPostsByAuthor(user.pk_user);
      const sparseData = {
        id: fetchedUser?.id,
        username: fetchedUser?.username,
        posts: posts.map(p => ({ id: p.id, title: p.title })),
      };
      const duration = performance.now() - start;
      sparseTimings.push(duration);
      expect(sparseData.posts.length).toBe(10);
    }

    // Assert
    const fullAvg = fullTimings.reduce((a, b) => a + b, 0) / fullTimings.length;
    const sparseAvg = sparseTimings.reduce((a, b) => a + b, 0) / sparseTimings.length;

    console.log(`Field selection - Full: ${fullAvg.toFixed(3)}ms, Sparse: ${sparseAvg.toFixed(3)}ms`);
    expect(fullAvg).toBeLessThan(20);
    expect(sparseAvg).toBeLessThan(20);
  });

  it('should handle nested list performance efficiently', () => {
    // Arrange
    const users = Array.from({ length: 10 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 5 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });
    const iterations = 30;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const nested = allUsers.map(user => ({
        ...user,
        posts: factory.getPostsByAuthor(user.pk_user),
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(nested.length).toBe(10);
      expect(nested.every(u => u.posts.length === 5)).toBe(true);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Nested lists (10 users, 5 posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should measure memory usage with large nested result set', () => {
    // Arrange
    const users = Array.from({ length: 20 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 10 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`, `Content ${i}`)
      );
    });
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const largeResult = allUsers.map(user => ({
        user,
        posts: factory.getPostsByAuthor(user.pk_user),
        metadata: {
          postCount: factory.getPostsByAuthor(user.pk_user).length,
          timestamp: new Date(),
        },
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(largeResult.length).toBe(20);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Large nested result (20 users, 10 posts, 200 total) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });

  it('should handle deep nesting stress test', () => {
    // Arrange - 4 levels: User -> Posts -> Comments -> Author
    const users = Array.from({ length: 3 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      const posts = Array.from({ length: 4 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
      posts.forEach(post => {
        Array.from({ length: 3 }, (_, i) =>
          factory.createTestComment(user.id, post.id, `Comment ${i}`)
        );
      });
    });
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const deepNested = allUsers.map(user => {
        const posts = factory.getPostsByAuthor(user.pk_user);
        return {
          user,
          postsWithComments: posts.map(post => {
            const comments = factory.getCommentsByPost(post.pk_post);
            return {
              post,
              commentsWithAuthors: comments.map(comment => ({
                comment,
                author: comment.author,
                authorPosts: factory.getPostsByAuthor(comment.fk_author),
              })),
            };
          }),
        };
      });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(deepNested.length).toBe(3);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const maxTime = Math.max(...timings);
    console.log(`Deep nesting stress test (4 levels) - Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(80);
  });

  it('should measure large result set handling', () => {
    // Arrange
    const user = factory.createTestUser('prolific', 'prolific@example.com', 'Prolific User');
    const posts = Array.from({ length: 100 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`, `Content ${i}`)
    );
    posts.forEach(post => {
      factory.createTestComment(user.id, post.id, 'Comment');
    });
    const iterations = 15;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const userPosts = factory.getPostsByAuthor(user.pk_user);
      const withComments = userPosts.map(post => ({
        ...post,
        comments: factory.getCommentsByPost(post.pk_post),
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(withComments.length).toBe(100);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Large result set (100 posts with comments) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(100);
  });

  it('should measure timeout handling for slow nested queries', () => {
    // Arrange
    const users = Array.from({ length: 50 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 5 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });
    const iterations = 10;
    const timings: number[] = [];
    const timeoutMs = 1000; // 1 second timeout

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const nested = allUsers.map(user => ({
        ...user,
        posts: factory.getPostsByAuthor(user.pk_user),
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(duration).toBeLessThan(timeoutMs);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    const maxTime = Math.max(...timings);
    console.log(`Timeout handling (${timeoutMs}ms limit) - Avg: ${avgTime.toFixed(3)}ms, Max: ${maxTime.toFixed(3)}ms`);
    expect(maxTime).toBeLessThan(timeoutMs);
  });

  it('should measure pagination impact on nested queries', () => {
    // Arrange
    const users = Array.from({ length: 20 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 20 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });
    const iterations = 20;
    const timings: number[] = [];
    const pageSize = 5;

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const paginatedUsers = allUsers.slice(0, 10);
      const nested = paginatedUsers.map(user => ({
        ...user,
        posts: factory.getPostsByAuthor(user.pk_user).slice(0, pageSize),
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(nested.length).toBe(10);
      expect(nested.every(u => u.posts.length === pageSize)).toBe(true);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Nested with pagination (10 users, ${pageSize} posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(40);
  });

  it('should measure performance of nested filtering', () => {
    // Arrange
    const users = Array.from({ length: 15 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 10 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`, i % 2 === 0 ? 'Published' : 'Draft')
      );
    });
    const iterations = 30;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const filtered = allUsers.map(user => {
        const allPosts = factory.getPostsByAuthor(user.pk_user);
        return {
          ...user,
          publishedPosts: allPosts.filter(p => p.content.includes('Published')),
        };
      });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(filtered.length).toBe(15);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Nested filtering (15 users, filter 10 posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(45);
  });
});
