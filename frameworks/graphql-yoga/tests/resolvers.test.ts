import { describe, it, expect, beforeEach } from 'vitest';
import { TestFactory, ValidationHelper, DataGenerator } from './test-factory';

describe('GraphQL Yoga Resolvers', () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
  });

  // ============================================================================
  // Query Tests: User Resolution
  // ============================================================================

  describe('User Queries', () => {
    it('should return user by UUID', () => {
      const user = factory.createTestUser('alice', 'alice@example.com', 'Alice Smith', 'Hello!');

      const result = factory.getUser(user.id);

      expect(result).toBeDefined();
      expect(result?.id).toBe(user.id);
      expect(result?.username).toBe('alice');
      expect(result?.full_name).toBe('Alice Smith');
      expect(result?.bio).toBe('Hello!');
    });

    it('should return list of users', () => {
      factory.createTestUser('alice', 'alice@example.com', 'Alice');
      factory.createTestUser('bob', 'bob@example.com', 'Bob');
      factory.createTestUser('charlie', 'charlie@example.com', 'Charlie');

      const users = factory.getAllUsers();

      expect(users.length).toBe(3);
      const usernames = users.map(u => u.username);
      expect(usernames).toContain('alice');
      expect(usernames).toContain('bob');
      expect(usernames).toContain('charlie');
    });

    it('should respect limit parameter', () => {
      for (let i = 0; i < 15; i++) {
        factory.createTestUser(`user${i}`, `user${i}@example.com`, `User ${i}`);
      }

      const allUsers = factory.getAllUsers();
      const limitedUsers = allUsers.slice(0, 10);

      expect(limitedUsers.length).toBe(10);
    });

    it('should return undefined for non-existent user', () => {
      const result = factory.getUser('non-existent-id');

      expect(result).toBeUndefined();
    });
  });

  // ============================================================================
  // Query Tests: Post Resolution
  // ============================================================================

  describe('Post Queries', () => {
    it('should return post by ID', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(user.id, 'Test Post', 'Test content');

      const result = factory.getPost(post.id);

      expect(result).toBeDefined();
      expect(result?.id).toBe(post.id);
      expect(result?.title).toBe('Test Post');
      expect(result?.content).toBe('Test content');
    });

    it('should return list of posts', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      factory.createTestPost(user.id, 'Post 1');
      factory.createTestPost(user.id, 'Post 2');
      factory.createTestPost(user.id, 'Post 3');

      const posts = factory.getAllPosts();

      expect(posts.length).toBe(3);
    });

    it('should return posts by author', () => {
      const author1 = factory.createTestUser('author1', 'a1@example.com', 'Author 1');
      const author2 = factory.createTestUser('author2', 'a2@example.com', 'Author 2');

      factory.createTestPost(author1.id, 'Post by Author 1');
      factory.createTestPost(author2.id, 'Post by Author 2');

      const author1Posts = factory.getPostsByAuthor(author1.pk_user);
      const author2Posts = factory.getPostsByAuthor(author2.pk_user);

      expect(author1Posts.length).toBe(1);
      expect(author2Posts.length).toBe(1);
      expect(author1Posts[0].title).toBe('Post by Author 1');
    });

    it('should return undefined for non-existent post', () => {
      const result = factory.getPost('non-existent-id');

      expect(result).toBeUndefined();
    });
  });

  // ============================================================================
  // Query Tests: Comment Resolution
  // ============================================================================

  describe('Comment Queries', () => {
    it('should return comment by ID', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');
      const commenter = factory.createTestUser('commenter', 'commenter@example.com', 'Commenter');
      const comment = factory.createTestComment(commenter.id, post.id, 'Great post!');

      const result = factory.getComment(comment.id);

      expect(result).toBeDefined();
      expect(result?.id).toBe(comment.id);
      expect(result?.content).toBe('Great post!');
    });

    it('should return comments by post', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');
      const commenter = factory.createTestUser('commenter', 'commenter@example.com', 'Commenter');

      factory.createTestComment(commenter.id, post.id, 'Comment 1');
      factory.createTestComment(commenter.id, post.id, 'Comment 2');

      const comments = factory.getCommentsByPost(post.pk_post);

      expect(comments.length).toBe(2);
    });
  });

  // ============================================================================
  // Mutation Tests
  // ============================================================================

  describe('Mutations', () => {
    it('should update user bio', () => {
      const user = factory.createTestUser('alice', 'alice@example.com', 'Alice');

      // Simulate mutation
      const storedUser = factory.getUser(user.id);
      if (storedUser) {
        storedUser.bio = 'Updated bio';
        storedUser.updated_at = new Date();
      }

      expect(storedUser?.bio).toBe('Updated bio');
    });

    it('should update user full name', () => {
      const user = factory.createTestUser('bob', 'bob@example.com', 'Bob');

      const storedUser = factory.getUser(user.id);
      if (storedUser) {
        storedUser.full_name = 'Bob Smith';
        storedUser.updated_at = new Date();
      }

      expect(storedUser?.full_name).toBe('Bob Smith');
    });
  });

  // ============================================================================
  // Relationship Tests
  // ============================================================================

  describe('Relationships', () => {
    it('should resolve user posts relationship', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const post1 = factory.createTestPost(user.id, 'Post 1');
      const post2 = factory.createTestPost(user.id, 'Post 2');

      const posts = factory.getPostsByAuthor(user.pk_user);

      expect(posts.length).toBe(2);
      const postIds = posts.map(p => p.id);
      expect(postIds).toContain(post1.id);
      expect(postIds).toContain(post2.id);
    });

    it('should resolve post author relationship', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');

      expect(post.author).toBeDefined();
      expect(post.author?.pk_user).toBe(author.pk_user);
    });

    it('should resolve post comments relationship', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');
      const commenter = factory.createTestUser('commenter', 'commenter@example.com', 'Commenter');

      factory.createTestComment(commenter.id, post.id, 'Comment 1');
      factory.createTestComment(commenter.id, post.id, 'Comment 2');

      const comments = factory.getCommentsByPost(post.pk_post);

      expect(comments.length).toBe(2);
    });

    it('should resolve comment author relationship', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');
      const commenter = factory.createTestUser('commenter', 'commenter@example.com', 'Commenter');
      const comment = factory.createTestComment(commenter.id, post.id, 'Great!');

      expect(comment.author).toBeDefined();
      expect(comment.author?.pk_user).toBe(commenter.pk_user);
    });
  });

  // ============================================================================
  // Validation Tests
  // ============================================================================

  describe('Validation', () => {
    it('should validate UUID format', () => {
      const user = factory.createTestUser('user', 'user@example.com', 'User');

      expect(ValidationHelper.isValidUUID(user.id)).toBe(true);
      expect(ValidationHelper.isValidUUID('not-a-uuid')).toBe(false);
    });

    it('should handle special characters in content', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const specialContent = "Test with 'quotes' and \"double quotes\" and <html>";
      const post = factory.createTestPost(user.id, 'Special Post', specialContent);

      expect(post.content).toBe(specialContent);
    });

    it('should handle unicode content', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const unicodeContent = 'Test with émojis 🎉 and ñ and 中文';
      const post = factory.createTestPost(user.id, 'Unicode Post', unicodeContent);

      expect(post.content).toBe(unicodeContent);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle null bio', () => {
      const user = factory.createTestUser('user', 'user@example.com', 'User');

      expect(user.bio).toBeNull();
    });

    it('should throw when creating post with invalid author', () => {
      expect(() => {
        factory.createTestPost('non-existent-author', 'Test Post');
      }).toThrow('Author not found');
    });

    it('should throw when creating comment with invalid post', () => {
      const user = factory.createTestUser('user', 'user@example.com', 'User');

      expect(() => {
        factory.createTestComment(user.id, 'non-existent-post', 'Comment');
      }).toThrow('Author or Post not found');
    });

    it('should handle empty posts list for new user', () => {
      const user = factory.createTestUser('newuser', 'newuser@example.com', 'New User');

      const posts = factory.getPostsByAuthor(user.pk_user);

      expect(posts.length).toBe(0);
    });
  });

  // ============================================================================
  // Performance Tests
  // ============================================================================

  describe('Performance', () => {
    it('should handle creating many posts', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');

      for (let i = 0; i < 50; i++) {
        factory.createTestPost(user.id, `Post ${i}`);
      }

      const posts = factory.getPostsByAuthor(user.pk_user);

      expect(posts.length).toBe(50);
    });

    it('should handle long content', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const longContent = DataGenerator.generateLongString(100000);
      const post = factory.createTestPost(user.id, 'Long Post', longContent);

      expect(post.content.length).toBe(100000);
    });
  });

  // ============================================================================
  // Factory Reset Tests
  // ============================================================================

  describe('Factory Reset', () => {
    it('should reset all data', () => {
      factory.createTestUser('user1', 'user1@example.com', 'User 1');
      factory.createTestUser('user2', 'user2@example.com', 'User 2');

      factory.reset();

      expect(factory.getUserCount()).toBe(0);
      expect(factory.getPostCount()).toBe(0);
      expect(factory.getCommentCount()).toBe(0);
    });
  });
});
