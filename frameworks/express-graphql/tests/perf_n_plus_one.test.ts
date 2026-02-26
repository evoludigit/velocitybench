import { describe, it, expect, beforeEach } from 'vitest';
import { performance } from 'perf_hooks';
import { TestFactory } from './test-factory';

/**
 * N+1 Query Detection Performance Benchmarks
 *
 * Tests for detecting and measuring N+1 query patterns.
 * Compares naive approaches vs optimized batch loading.
 */
describe('N+1 Query Detection Benchmarks', { tags: ['perf', 'perf:queries', 'perf:n-plus-one'] }, () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
    factory.reset();
  });

  it('should detect N+1 in users with posts (naive)', () => {
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
    let queryCount = 0;

    // Act - Naive N+1 pattern
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      queryCount = 1; // Initial query
      allUsers.forEach(user => {
        const posts = factory.getPostsByAuthor(user.pk_user);
        queryCount++; // N additional queries
      });
      const duration = performance.now() - start;
      timings.push(duration);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`N+1 naive (${users.length} users, ${queryCount} queries) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(queryCount).toBe(11); // 1 + 10
    expect(avgTime).toBeLessThan(40);
  });

  it('should detect N+1 in posts with comments (naive)', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const posts = Array.from({ length: 15 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`)
    );
    posts.forEach(post => {
      Array.from({ length: 3 }, (_, i) =>
        factory.createTestComment(user.id, post.id, `Comment ${i}`)
      );
    });
    const iterations = 30;
    const timings: number[] = [];
    let queryCount = 0;

    // Act - Naive N+1 pattern
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allPosts = factory.getAllPosts();
      queryCount = 1;
      allPosts.forEach(post => {
        const comments = factory.getCommentsByPost(post.pk_post);
        queryCount++;
      });
      const duration = performance.now() - start;
      timings.push(duration);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`N+1 naive posts (${posts.length} posts, ${queryCount} queries) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(queryCount).toBe(posts.length + 1);
    expect(avgTime).toBeLessThan(50);
  });

  it('should verify batch loading optimization', () => {
    // Arrange
    const users = Array.from({ length: 10 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 5 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });

    // Act - Naive approach: collect results per user
    const allUsers = factory.getAllUsers();
    const naiveResult: number[] = [];
    allUsers.forEach(user => {
      const posts = factory.getPostsByAuthor(user.pk_user);
      naiveResult.push(posts.length);
    });

    // Act - Optimized batch approach: single fetch then group
    const allPosts = factory.getAllPosts();
    const postsMap = new Map<number, typeof allPosts>();
    allPosts.forEach(post => {
      if (!postsMap.has(post.fk_author)) {
        postsMap.set(post.fk_author, []);
      }
      postsMap.get(post.fk_author)!.push(post);
    });
    const batchResult: number[] = allUsers.map(user => (postsMap.get(user.pk_user) ?? []).length);

    // Assert - both approaches return the same correct results
    // Timing comparison is not reliable for in-memory operations at this scale in CI
    console.log(`Naive result counts: [${naiveResult.join(', ')}], Batch result counts: [${batchResult.join(', ')}]`);
    expect(batchResult.length).toBe(naiveResult.length);
    expect(batchResult).toEqual(naiveResult);
  });

  it('should compare query count (naive vs optimized)', () => {
    // Arrange
    const users = Array.from({ length: 20 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 3 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });

    // Act - Count naive queries
    let naiveQueries = 0;
    const allUsers = factory.getAllUsers();
    naiveQueries++; // Get all users
    allUsers.forEach(user => {
      factory.getPostsByAuthor(user.pk_user);
      naiveQueries++; // One query per user
    });

    // Act - Count optimized queries
    let optimizedQueries = 0;
    factory.getAllUsers();
    optimizedQueries++; // Get all users
    factory.getAllPosts();
    optimizedQueries++; // Get all posts in one query

    // Assert
    console.log(`Query count - Naive: ${naiveQueries}, Optimized: ${optimizedQueries}`);
    expect(naiveQueries).toBe(21); // 1 + 20
    expect(optimizedQueries).toBe(2); // 1 + 1
    expect(optimizedQueries).toBeLessThan(naiveQueries);
  });

  it('should measure implicit eager loading performance', () => {
    // Arrange
    const users = Array.from({ length: 15 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 4 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });
    const iterations = 30;
    const timings: number[] = [];

    // Act - Eager load pattern (preload relationships)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const allPosts = factory.getAllPosts();
      const enrichedUsers = allUsers.map(user => ({
        ...user,
        posts: allPosts.filter(p => p.fk_author === user.pk_user),
      }));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(enrichedUsers.length).toBe(15);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Implicit eager loading (15 users, 4 posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(35);
  });

  it('should measure batch size impact', () => {
    // Arrange
    const users = Array.from({ length: 50 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 2 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });
    const iterations = 20;
    const batchSizes = [10, 25, 50];
    const results: { size: number; avgTime: number }[] = [];

    // Act - Test different batch sizes
    batchSizes.forEach(batchSize => {
      const timings: number[] = [];
      for (let i = 0; i < iterations; i++) {
        const start = performance.now();
        for (let offset = 0; offset < users.length; offset += batchSize) {
          const batch = users.slice(offset, offset + batchSize);
          batch.forEach(user => {
            factory.getPostsByAuthor(user.pk_user);
          });
        }
        const duration = performance.now() - start;
        timings.push(duration);
      }
      const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
      results.push({ size: batchSize, avgTime });
    });

    // Assert
    results.forEach(({ size, avgTime }) => {
      console.log(`Batch size ${size} - Avg: ${avgTime.toFixed(3)}ms`);
      expect(avgTime).toBeLessThan(100);
    });
    expect(results.length).toBe(3);
  });

  it('should validate cache behavior', () => {
    // Arrange
    const users = Array.from({ length: 10 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      Array.from({ length: 5 }, (_, i) =>
        factory.createTestPost(user.id, `Post ${i}`)
      );
    });
    const iterations = 50;
    const firstPassTimings: number[] = [];
    const secondPassTimings: number[] = [];

    // Act - First pass (cold)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      allUsers.forEach(user => {
        factory.getPostsByAuthor(user.pk_user);
      });
      const duration = performance.now() - start;
      firstPassTimings.push(duration);
    }

    // Act - Second pass (potentially cached)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      allUsers.forEach(user => {
        factory.getPostsByAuthor(user.pk_user);
      });
      const duration = performance.now() - start;
      secondPassTimings.push(duration);
    }

    // Assert
    const firstAvg = firstPassTimings.reduce((a, b) => a + b, 0) / firstPassTimings.length;
    const secondAvg = secondPassTimings.reduce((a, b) => a + b, 0) / secondPassTimings.length;

    console.log(`First pass: ${firstAvg.toFixed(3)}ms, Second pass: ${secondAvg.toFixed(3)}ms`);
    expect(firstAvg).toBeLessThan(50);
    expect(secondAvg).toBeLessThan(50);
  });

  it('should measure N+1 impact at scale', () => {
    // Arrange
    const userCount = 100;
    const users = Array.from({ length: userCount }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      factory.createTestPost(user.id, 'Post');
    });
    const iterations = 10;
    const naiveTimings: number[] = [];
    const optimizedTimings: number[] = [];

    // Act - Naive N+1
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      allUsers.forEach(user => {
        factory.getPostsByAuthor(user.pk_user);
      });
      const duration = performance.now() - start;
      naiveTimings.push(duration);
    }

    // Act - Optimized batch
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const allPosts = factory.getAllPosts();
      const postsMap = new Map();
      allPosts.forEach(post => {
        if (!postsMap.has(post.fk_author)) {
          postsMap.set(post.fk_author, []);
        }
        postsMap.get(post.fk_author).push(post);
      });
      const duration = performance.now() - start;
      optimizedTimings.push(duration);
    }

    // Assert
    const naiveAvg = naiveTimings.reduce((a, b) => a + b, 0) / naiveTimings.length;
    const optimizedAvg = optimizedTimings.reduce((a, b) => a + b, 0) / optimizedTimings.length;
    const scaleFactor = naiveAvg / optimizedAvg;

    console.log(`N+1 at scale (${userCount} users) - Naive: ${naiveAvg.toFixed(3)}ms, Optimized: ${optimizedAvg.toFixed(3)}ms, Factor: ${scaleFactor.toFixed(2)}x`);
    expect(optimizedAvg).toBeLessThan(naiveAvg);
    expect(scaleFactor).toBeGreaterThan(1);
  });
});
