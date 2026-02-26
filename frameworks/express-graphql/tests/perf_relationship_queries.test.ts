import { describe, it, expect, beforeEach } from 'vitest';
import { performance } from 'perf_hooks';
import { TestFactory } from './test-factory';

/**
 * Relationship Query Performance Benchmarks
 *
 * Tests performance of queries involving entity relationships
 * (1-to-many, many-to-1, nested relationships).
 */
describe('Relationship Query Performance Benchmarks', { tags: ['perf', 'perf:queries', 'perf:relationships'] }, () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
    factory.reset();
  });

  it('should resolve user with posts (1-to-many) efficiently', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    Array.from({ length: 10 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`, `Content ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const posts = factory.getPostsByAuthor(user.pk_user);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(fetchedUser).toBeDefined();
      expect(posts.length).toBe(10);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`User with posts (10 posts) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(15);
  });

  it('should resolve posts with comments (1-to-many) efficiently', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const post = factory.createTestPost(user.id, 'Post');
    Array.from({ length: 20 }, (_, i) =>
      factory.createTestComment(user.id, post.id, `Comment ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedPost = factory.getPost(post.id);
      const comments = factory.getCommentsByPost(post.pk_post);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(fetchedPost).toBeDefined();
      expect(comments.length).toBe(20);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Post with comments (20 comments) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(15);
  });

  it('should resolve comments with author (many-to-1) efficiently', () => {
    // Arrange
    const author = factory.createTestUser('author', 'author@example.com', 'Author');
    const post = factory.createTestPost(author.id, 'Post');
    const comments = Array.from({ length: 15 }, (_, i) =>
      factory.createTestComment(author.id, post.id, `Comment ${i}`)
    );
    const iterations = 50;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const comment = comments[Math.floor(Math.random() * comments.length)];
      const start = performance.now();
      const fetchedComment = factory.getComment(comment.id);
      const commentAuthor = fetchedComment?.author;
      const duration = performance.now() - start;
      timings.push(duration);
      expect(commentAuthor).toBeDefined();
      expect(commentAuthor?.pk_user).toBe(author.pk_user);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Comment with author - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(10);
  });

  it('should measure 2-level nesting performance', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    const posts = Array.from({ length: 5 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`)
    );
    posts.forEach(post => {
      Array.from({ length: 3 }, (_, i) =>
        factory.createTestComment(user.id, post.id, `Comment ${i}`)
      );
    });
    const iterations = 50;
    const timings: number[] = [];

    // Act - User -> Posts -> Comments
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const userPosts = factory.getPostsByAuthor(user.pk_user);
      const allComments = userPosts.flatMap(p => factory.getCommentsByPost(p.pk_post));
      const duration = performance.now() - start;
      timings.push(duration);
      expect(fetchedUser).toBeDefined();
      expect(userPosts.length).toBe(5);
      expect(allComments.length).toBe(15);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`2-level nesting (User->Posts->Comments) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(25);
  });

  it('should measure 3-level nesting performance', () => {
    // Arrange
    const users = Array.from({ length: 3 }, (_, i) =>
      factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`)
    );
    users.forEach(user => {
      const posts = Array.from({ length: 2 }, (_, i) =>
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

    // Act - Users -> Posts -> Comments -> Authors
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const results = allUsers.map(user => {
        const posts = factory.getPostsByAuthor(user.pk_user);
        return posts.map(post => {
          const comments = factory.getCommentsByPost(post.pk_post);
          return comments.map(comment => comment.author);
        });
      });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(results.length).toBe(3);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`3-level nesting (Users->Posts->Comments->Authors) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(40);
  });

  it('should compare eager-load vs lazy-load patterns', () => {
    // Arrange
    const user = factory.createTestUser('author', 'author@example.com', 'Author');
    Array.from({ length: 20 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`)
    );
    const iterations = 50;
    const eagerTimings: number[] = [];
    const lazyTimings: number[] = [];

    // Act - Eager loading pattern (get all at once)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const posts = factory.getPostsByAuthor(user.pk_user);
      const duration = performance.now() - start;
      eagerTimings.push(duration);
      expect(posts.length).toBe(20);
    }

    // Act - Lazy loading pattern (individual queries)
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const allPosts = factory.getAllPosts();
      const userPosts = allPosts.filter(p => p.fk_author === user.pk_user);
      const duration = performance.now() - start;
      lazyTimings.push(duration);
      expect(userPosts.length).toBe(20);
    }

    // Assert
    const eagerAvg = eagerTimings.reduce((a, b) => a + b, 0) / eagerTimings.length;
    const lazyAvg = lazyTimings.reduce((a, b) => a + b, 0) / lazyTimings.length;

    console.log(`Eager loading: ${eagerAvg.toFixed(3)}ms, Lazy loading: ${lazyAvg.toFixed(3)}ms`);
    expect(eagerAvg).toBeLessThan(20);
    expect(lazyAvg).toBeLessThan(25);
  });

  it('should measure batch loading efficiency', () => {
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

    // Act - Batch load posts for all users
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const allUsers = factory.getAllUsers();
      const postsMap = new Map();
      allUsers.forEach(user => {
        const posts = factory.getPostsByAuthor(user.pk_user);
        postsMap.set(user.id, posts);
      });
      const duration = performance.now() - start;
      timings.push(duration);
      expect(postsMap.size).toBe(10);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Batch loading (10 users, 5 posts each) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(30);
  });

  it('should handle many relationships efficiently', () => {
    // Arrange
    const user = factory.createTestUser('prolific', 'prolific@example.com', 'Prolific User');
    Array.from({ length: 100 }, (_, i) =>
      factory.createTestPost(user.id, `Post ${i}`)
    );
    const iterations = 20;
    const timings: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      const fetchedUser = factory.getUser(user.id);
      const posts = factory.getPostsByAuthor(user.pk_user);
      const duration = performance.now() - start;
      timings.push(duration);
      expect(posts.length).toBe(100);
    }

    // Assert
    const avgTime = timings.reduce((a, b) => a + b, 0) / timings.length;
    console.log(`Many relationships (100 posts) - Avg: ${avgTime.toFixed(3)}ms`);
    expect(avgTime).toBeLessThan(50);
  });
});
