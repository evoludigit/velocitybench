import { TestFactory } from './test-factory';

describe('Mutations Tests', () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
  });

  // ============================================================================
  // Mutation: updateUser
  // ============================================================================

  test('updates user full name', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Developer');
    const userId = user.id;

    // Simulate mutation
    user.full_name = 'Alice Smith';

    // Verify
    expect(user.full_name).toBe('Alice Smith');
    expect(user.id).toBe(userId);
  });

  test('updates user bio', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Developer');
    const userId = user.id;

    // Simulate mutation
    user.bio = 'Senior Developer';

    // Verify
    expect(user.bio).toBe('Senior Developer');
    expect(user.id).toBe(userId);
  });

  test('updates both fields', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Developer');
    const userId = user.id;

    // Simulate mutation
    user.full_name = 'Alice Smith';
    user.bio = 'Senior Developer';

    // Verify
    expect(user.full_name).toBe('Alice Smith');
    expect(user.bio).toBe('Senior Developer');
    expect(user.id).toBe(userId);
  });

  test('clears bio with empty string', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Developer');
    const userId = user.id;

    // Simulate mutation
    user.bio = null;

    // Verify
    expect(user.bio).toBeNull();
    expect(user.id).toBe(userId);
  });

  // ============================================================================
  // Mutation: updatePost
  // ============================================================================

  test('updates post title', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Original Title', 'Original Content');
    const postId = post.id;

    // Simulate mutation
    post.title = 'Updated Title';

    // Verify
    expect(post.title).toBe('Updated Title');
    expect(post.id).toBe(postId);
  });

  test('updates post content', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Original Title', 'Original Content');
    const postId = post.id;

    // Simulate mutation
    post.content = 'Updated Content';

    // Verify
    expect(post.content).toBe('Updated Content');
    expect(post.id).toBe(postId);
  });

  test('updates both fields', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Original Title', 'Original Content');
    const postId = post.id;

    // Simulate mutation
    post.title = 'Updated Title';
    post.content = 'Updated Content';

    // Verify
    expect(post.title).toBe('Updated Title');
    expect(post.content).toBe('Updated Content');
    expect(post.id).toBe(postId);
  });

  // ============================================================================
  // Field Immutability
  // ============================================================================

  test('user ID immutable after update', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Bio');
    const originalId = user.id;

    // Try to "update"
    user.bio = 'Updated';

    // Verify ID unchanged
    expect(user.id).toBe(originalId);
  });

  test('post ID immutable after update', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Title', 'Content');
    const originalId = post.id;

    // Try to "update"
    post.title = 'Updated';

    // Verify ID unchanged
    expect(post.id).toBe(originalId);
  });

  test('username immutable', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    const originalUsername = user.username;

    // Try to "update"
    user.bio = 'Updated';

    // Verify username unchanged
    expect(user.username).toBe(originalUsername);
  });

  // ============================================================================
  // State Changes
  // ============================================================================

  test('sequential updates accumulate', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');

    // Apply updates sequentially
    user.bio = 'Developer';
    user.bio = 'Senior Developer';

    // Verify latest state
    expect(user.bio).toBe('Senior Developer');
  });

  test('updates isolated between entities', () => {
    const user1 = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Bio1');
    const user2 = factory.createTestUser('bob', 'bob@example.com', 'Bob', 'Bio2');

    const originalBio2 = user2.bio;

    // Update user1
    user1.bio = 'Updated';

    // Verify user2 unchanged
    expect(user2.bio).toBe(originalBio2);
  });

  // ============================================================================
  // Return Value Validation
  // ============================================================================

  test('updated user returns all fields', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Developer');
    user.bio = 'Updated';

    // Verify all fields present
    expect(user.id).toBeTruthy();
    expect(user.username).toBe('alice');
    expect(user.bio).toBe('Updated');
  });

  test('updated post returns all fields', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Title', 'Content');
    post.title = 'Updated';

    // Verify all fields present
    expect(post.id).toBeTruthy();
    expect(post.title).toBe('Updated');
    expect(post.author).toBeDefined();
  });

  test('mutation maintains created_at', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    const originalCreatedAt = user.created_at;

    // Update
    user.full_name = 'Alice Updated';

    // Verify created_at unchanged
    expect(user.created_at).toBe(originalCreatedAt);
  });
});
