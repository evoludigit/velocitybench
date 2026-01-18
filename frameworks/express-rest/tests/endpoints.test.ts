import { describe, it, expect, beforeEach } from 'vitest';
import { TestFactory, ValidationHelper, DataGenerator } from './test-factory';

describe('Express REST Endpoints', () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
  });

  // ============================================================================
  // GET /users Tests
  // ============================================================================

  describe('GET /users', () => {
    it('should return user by UUID', () => {
      const user = factory.createTestUser('alice', 'alice@example.com', 'Alice Smith', 'Hello!');
      const result = factory.getUser(user.id);

      expect(result).toBeDefined();
      expect(result?.id).toBe(user.id);
      expect(result?.username).toBe('alice');
      expect(result?.full_name).toBe('Alice Smith');
    });

    it('should return list of users', () => {
      factory.createTestUser('alice', 'alice@example.com', 'Alice');
      factory.createTestUser('bob', 'bob@example.com', 'Bob');
      factory.createTestUser('charlie', 'charlie@example.com', 'Charlie');

      const users = factory.getAllUsers();
      expect(users.length).toBe(3);
    });

    it('should return undefined for non-existent user', () => {
      const result = factory.getUser('non-existent-id');
      expect(result).toBeUndefined();
    });
  });

  // ============================================================================
  // GET /posts Tests
  // ============================================================================

  describe('GET /posts', () => {
    it('should return post by ID', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(user.id, 'Test Post', 'Test content');

      const result = factory.getPost(post.id);
      expect(result).toBeDefined();
      expect(result?.title).toBe('Test Post');
    });

    it('should return posts by author', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      factory.createTestPost(author.id, 'Post 1');
      factory.createTestPost(author.id, 'Post 2');

      const posts = factory.getPostsByAuthor(author.pk_user);
      expect(posts.length).toBe(2);
    });
  });

  // ============================================================================
  // GET /comments Tests
  // ============================================================================

  describe('GET /comments', () => {
    it('should return comment by ID', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');
      const commenter = factory.createTestUser('commenter', 'commenter@example.com', 'Commenter');
      const comment = factory.createTestComment(commenter.id, post.id, 'Great post!');

      const result = factory.getComment(comment.id);
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
  // Relationship Tests
  // ============================================================================

  describe('Relationships', () => {
    it('should resolve user posts', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      factory.createTestPost(user.id, 'Post 1');
      factory.createTestPost(user.id, 'Post 2');

      const posts = factory.getPostsByAuthor(user.pk_user);
      expect(posts.length).toBe(2);
    });

    it('should resolve post author', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');

      expect(post.author?.pk_user).toBe(author.pk_user);
    });

    it('should resolve comment author', () => {
      const author = factory.createTestUser('author', 'author@example.com', 'Author');
      const post = factory.createTestPost(author.id, 'Test Post');
      const commenter = factory.createTestUser('commenter', 'commenter@example.com', 'Commenter');
      const comment = factory.createTestComment(commenter.id, post.id, 'Great!');

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
    });

    it('should handle special characters', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const specialContent = "Test with 'quotes' and <html>";
      const post = factory.createTestPost(user.id, 'Special', specialContent);

      expect(post.content).toBe(specialContent);
    });

    it('should handle unicode', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const unicodeContent = 'Test with 🎉 and 中文';
      const post = factory.createTestPost(user.id, 'Unicode', unicodeContent);

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

    it('should throw for invalid author', () => {
      expect(() => factory.createTestPost('invalid', 'Test')).toThrow();
    });

    it('should handle empty posts list', () => {
      const user = factory.createTestUser('newuser', 'new@example.com', 'New');
      expect(factory.getPostsByAuthor(user.pk_user).length).toBe(0);
    });
  });

  // ============================================================================
  // Performance Tests
  // ============================================================================

  describe('Performance', () => {
    it('should handle many posts', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      for (let i = 0; i < 50; i++) {
        factory.createTestPost(user.id, `Post ${i}`);
      }

      expect(factory.getPostsByAuthor(user.pk_user).length).toBe(50);
    });

    it('should handle long content', () => {
      const user = factory.createTestUser('author', 'author@example.com', 'Author');
      const longContent = DataGenerator.generateLongString(100000);
      const post = factory.createTestPost(user.id, 'Long', longContent);

      expect(post.content.length).toBe(100000);
    });
  });
});
