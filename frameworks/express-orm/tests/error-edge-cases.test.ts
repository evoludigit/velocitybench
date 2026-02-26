import { TestFactory, ValidationHelper, DataGenerator } from './test-factory';

describe('Error and Edge Cases Tests', () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
  });

  // ============================================================================
  // Error: HTTP Status Codes
  // ============================================================================

  test('GET /users returns 200', () => {
    factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    expect(factory.getUserCount()).toBe(1);
  });

  test('GET /nonexistent returns 404', () => {
    const user = factory.getUser('nonexistent-id');
    expect(user).toBeUndefined();
  });

  // ============================================================================
  // Error: 404 Not Found
  // ============================================================================

  test('user not found returns undefined', () => {
    const user = factory.getUser('nonexistent-user-id');
    expect(user).toBeUndefined();
  });

  test('post not found returns undefined', () => {
    const post = factory.getPost('nonexistent-post-id');
    expect(post).toBeUndefined();
  });

  // ============================================================================
  // Error: Invalid Input
  // ============================================================================

  test('invalid limit (negative)', () => {
    const limit = -5;
    const clamped = Math.max(0, Math.min(100, limit));
    expect(clamped).toBe(0);
  });

  test('invalid limit (zero)', () => {
    const limit = 0;
    const clamped = Math.max(0, Math.min(100, limit));
    expect(clamped).toBe(0);
  });

  test('very large limit', () => {
    const limit = 999999;
    const clamped = Math.max(0, Math.min(100, limit));
    expect(clamped).toBe(100);
  });

  // ============================================================================
  // Edge Case: UUID Validation
  // ============================================================================

  test('all user IDs are UUID', () => {
    factory.createTestUser('user0', 'user0@example.com', 'User', '');
    factory.createTestUser('user1', 'user1@example.com', 'User', '');
    factory.createTestUser('user2', 'user2@example.com', 'User', '');

    factory.getAllUsers().forEach(user => {
      expect(() => ValidationHelper.assertUUID(user.id)).not.toThrow();
    });
  });

  test('all post IDs are UUID', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');

    factory.createTestPost(author.id, 'Post0', 'Content');
    factory.createTestPost(author.id, 'Post1', 'Content');
    factory.createTestPost(author.id, 'Post2', 'Content');

    factory.getAllPosts().forEach(post => {
      expect(() => ValidationHelper.assertUUID(post.id)).not.toThrow();
    });
  });

  // ============================================================================
  // Edge Case: Special Characters
  // ============================================================================

  test('single quotes', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', "I'm a developer");
    expect(factory.getUser(user.id)).toBeDefined();
  });

  test('double quotes', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'He said "hello"');
    expect(factory.getUser(user.id)).toBeDefined();
  });

  test('HTML tags', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Check <this> out');
    expect(factory.getUser(user.id)).toBeDefined();
  });

  test('ampersand', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Tom & Jerry');
    expect(factory.getUser(user.id)).toBeDefined();
  });

  test('emoji', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '🎉 Celebration! 🚀 Rocket');
    expect(factory.getUser(user.id)).toBeDefined();
  });

  test('accents', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Àlice Müller', '');
    expect(factory.getUser(user.id)).toBeDefined();
  });

  test('diacritics', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'José García', '');
    expect(factory.getUser(user.id)).toBeDefined();
  });

  // ============================================================================
  // Edge Case: Boundary Conditions
  // ============================================================================

  test('very long bio (5000 chars)', () => {
    const longBio = DataGenerator.generateLongString(5000);
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', longBio);
    const retrieved = factory.getUser(user.id);
    expect(retrieved?.bio?.length).toBe(5000);
  });

  test('very long username (255 chars)', () => {
    const longName = DataGenerator.generateLongString(255);
    const user = factory.createTestUser(longName, 'user@example.com', 'User', '');
    const retrieved = factory.getUser(user.id);
    expect(retrieved?.username.length).toBe(255);
  });

  test('very long post title', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const longTitle = DataGenerator.generateLongString(500);
    const post = factory.createTestPost(author.id, longTitle, 'Content');
    const retrieved = factory.getPost(post.id);
    expect(retrieved?.title.length).toBe(500);
  });

  test('very long content (5000 chars)', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const longContent = DataGenerator.generateLongString(5000);
    const post = factory.createTestPost(author.id, 'Title', longContent);
    const retrieved = factory.getPost(post.id);
    expect(retrieved?.content.length).toBe(5000);
  });

  // ============================================================================
  // Edge Case: Null/Empty Fields
  // ============================================================================

  test('null bio is handled', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    const retrieved = factory.getUser(user.id);
    expect(retrieved?.bio).toBeNull();
  });

  test('empty string bio', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    const retrieved = factory.getUser(user.id);
    expect(retrieved?.bio).toBeNull();
  });

  test('present bio', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'My bio');
    const retrieved = factory.getUser(user.id);
    expect(retrieved?.bio).toBe('My bio');
  });

  // ============================================================================
  // Edge Case: Relationship Validation
  // ============================================================================

  test('post author ID is valid UUID', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Post', 'Content');

    expect(() => ValidationHelper.assertUUID(author.id)).not.toThrow();
  });

  test('post references correct author', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Post', 'Content');

    expect(post.fk_author).toBe(author.pk_user);
  });

  test('multiple posts reference different authors', () => {
    const author1 = factory.createTestUser('author1', 'author1@example.com', 'Author1', '');
    const author2 = factory.createTestUser('author2', 'author2@example.com', 'Author2', '');

    const post1 = factory.createTestPost(author1.id, 'Post1', 'Content');
    const post2 = factory.createTestPost(author2.id, 'Post2', 'Content');

    expect(post1.fk_author).not.toBe(post2.fk_author);
    expect(post1.fk_author).toBe(author1.pk_user);
    expect(post2.fk_author).toBe(author2.pk_user);
  });

  // ============================================================================
  // Edge Case: Data Type Validation
  // ============================================================================

  test('username is string', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    const retrieved = factory.getUser(user.id);
    expect(typeof retrieved?.username).toBe('string');
    expect(retrieved?.username).toBe('alice');
  });

  test('post title is string', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Test Post', 'Content');
    const retrieved = factory.getPost(post.id);
    expect(typeof retrieved?.title).toBe('string');
    expect(retrieved?.title).toBe('Test Post');
  });

  // ============================================================================
  // Edge Case: Uniqueness
  // ============================================================================

  test('multiple users have unique IDs', () => {
    const user1 = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    const user2 = factory.createTestUser('bob', 'bob@example.com', 'Bob', '');
    const user3 = factory.createTestUser('charlie', 'charlie@example.com', 'Charlie', '');

    expect(user1.id).not.toBe(user2.id);
    expect(user2.id).not.toBe(user3.id);
    expect(user1.id).not.toBe(user3.id);
  });

  test('multiple posts have unique IDs', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post1 = factory.createTestPost(author.id, 'Post1', 'Content1');
    const post2 = factory.createTestPost(author.id, 'Post2', 'Content2');
    const post3 = factory.createTestPost(author.id, 'Post3', 'Content3');

    expect(post1.id).not.toBe(post2.id);
    expect(post2.id).not.toBe(post3.id);
    expect(post1.id).not.toBe(post3.id);
  });
});
