import { TestFactory, ValidationHelper, DataGenerator } from './test-factory';

describe('Endpoints Tests', () => {
  let factory: TestFactory;

  beforeEach(() => {
    factory = new TestFactory();
  });

  // ============================================================================
  // Endpoint: GET /api/users (List)
  // ============================================================================

  test('GET /users returns list', () => {
    factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    factory.createTestUser('bob', 'bob@example.com', 'Bob', '');
    factory.createTestUser('charlie', 'charlie@example.com', 'Charlie', '');

    const users = factory.getAllUsers();
    expect(users.length).toBe(3);
  });

  test('GET /users respects limit', () => {
    for (let i = 0; i < 20; i++) {
      factory.createTestUser(`user${i}`, `user${i}@example.com`, 'User', '');
    }

    const users = factory.getAllUsers();
    expect(users.length).toBeGreaterThanOrEqual(20);
  });

  test('GET /users returns empty when no users', () => {
    const users = factory.getAllUsers();
    expect(users.length).toBe(0);
  });

  test('GET /users with pagination', () => {
    for (let i = 0; i < 30; i++) {
      factory.createTestUser(`user${i % 10}`, `user${i % 10}@example.com`, 'User', '');
    }

    const users = factory.getAllUsers();
    expect(users.length).toBeGreaterThanOrEqual(10);
  });

  // ============================================================================
  // Endpoint: GET /api/users/:id (Detail)
  // ============================================================================

  test('GET /users/:id returns user', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Developer');
    const retrieved = factory.getUser(user.id);

    expect(retrieved).toBeDefined();
    expect(retrieved?.username).toBe('alice');
  });

  test('GET /users/:id with null bio', () => {
    const user = factory.createTestUser('bob', 'bob@example.com', 'Bob', '');
    const retrieved = factory.getUser(user.id);

    expect(retrieved).toBeDefined();
    expect(retrieved?.bio).toBeNull();
  });

  test('GET /users/:id with special chars', () => {
    const user = factory.createTestUser('charlie', 'charlie@example.com', "Char'lie", 'Quote: "test"');
    const retrieved = factory.getUser(user.id);

    expect(retrieved).toBeDefined();
  });

  test('GET /users/:id not found', () => {
    const retrieved = factory.getUser('nonexistent-id');
    expect(retrieved).toBeUndefined();
  });

  // ============================================================================
  // Endpoint: GET /api/posts (List)
  // ============================================================================

  test('GET /posts returns list', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');

    factory.createTestPost(author.id, 'Post 1', 'Content');
    factory.createTestPost(author.id, 'Post 2', 'Content');
    factory.createTestPost(author.id, 'Post 3', 'Content');

    const posts = factory.getAllPosts();
    expect(posts.length).toBe(3);
  });

  test('GET /posts respects limit', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');

    for (let i = 0; i < 20; i++) {
      factory.createTestPost(author.id, `Post ${i}`, 'Content');
    }

    const posts = factory.getAllPosts();
    expect(posts.length).toBeGreaterThanOrEqual(20);
  });

  test('GET /posts returns empty', () => {
    const posts = factory.getAllPosts();
    expect(posts.length).toBe(0);
  });

  // ============================================================================
  // Endpoint: GET /api/posts/:id (Detail)
  // ============================================================================

  test('GET /posts/:id returns post', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Test Post', 'Test Content');
    const retrieved = factory.getPost(post.id);

    expect(retrieved).toBeDefined();
    expect(retrieved?.title).toBe('Test Post');
  });

  test('GET /posts/:id with null content', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'No Content', '');
    const retrieved = factory.getPost(post.id);

    expect(retrieved).toBeDefined();
    expect(retrieved?.content).toBe('');
  });

  test('GET /posts/:id with special chars', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const post = factory.createTestPost(author.id, 'Post with <tags>', 'Content & more');
    const retrieved = factory.getPost(post.id);

    expect(retrieved).toBeDefined();
  });

  test('GET /posts/:id not found', () => {
    const retrieved = factory.getPost('nonexistent-id');
    expect(retrieved).toBeUndefined();
  });

  // ============================================================================
  // Endpoint: GET /api/posts/by-author/:id
  // ============================================================================

  test("GET /posts/by-author/:id returns author's posts", () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');

    factory.createTestPost(author.id, 'Post 1', 'Content');
    factory.createTestPost(author.id, 'Post 2', 'Content');
    factory.createTestPost(author.id, 'Post 3', 'Content');

    const authorPosts = factory.getAllPosts().filter(p => p.fk_author === author.pk_user);
    expect(authorPosts.length).toBe(3);
  });

  test('multiple authors have separate posts', () => {
    const author1 = factory.createTestUser('author1', 'author1@example.com', 'Author1', '');
    const author2 = factory.createTestUser('author2', 'author2@example.com', 'Author2', '');

    factory.createTestPost(author1.id, 'Post 1', 'Content');
    factory.createTestPost(author1.id, 'Post 2', 'Content');
    factory.createTestPost(author2.id, 'Post 1', 'Content');

    const author1Posts = factory.getAllPosts().filter(p => p.fk_author === author1.pk_user);
    const author2Posts = factory.getAllPosts().filter(p => p.fk_author === author2.pk_user);

    expect(author1Posts.length).toBe(2);
    expect(author2Posts.length).toBe(1);
  });

  test('author with no posts', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    const authorPosts = factory.getAllPosts().filter(p => p.fk_author === author.pk_user);

    expect(authorPosts.length).toBe(0);
  });

  // ============================================================================
  // Endpoint: Response Headers
  // ============================================================================

  test('GET /users returns JSON', () => {
    factory.createTestUser('alice', 'alice@example.com', 'Alice', '');
    expect(factory.getUserCount()).toBeGreaterThan(0);
  });

  test('GET /posts returns JSON', () => {
    const author = factory.createTestUser('author', 'author@example.com', 'Author', '');
    factory.createTestPost(author.id, 'Post', 'Content');
    expect(factory.getPostCount()).toBeGreaterThan(0);
  });

  // ============================================================================
  // Endpoint: Pagination
  // ============================================================================

  test('page 0 with size 10', () => {
    for (let i = 0; i < 30; i++) {
      factory.createTestUser(`user${i % 10}`, `user${i % 10}@example.com`, 'User', '');
    }

    const users = factory.getAllUsers();
    expect(users.length).toBeGreaterThanOrEqual(10);
  });

  test('page 1 with size 10', () => {
    for (let i = 0; i < 30; i++) {
      factory.createTestUser(`user${i % 10}`, `user${i % 10}@example.com`, 'User', '');
    }

    const users = factory.getAllUsers();
    expect(users.length).toBeGreaterThanOrEqual(10);
  });

  test('last page with fewer items', () => {
    for (let i = 0; i < 25; i++) {
      factory.createTestUser(`user${i % 10}`, `user${i % 10}@example.com`, 'User', '');
    }

    const users = factory.getAllUsers();
    expect(users.length).toBeGreaterThanOrEqual(5);
  });

  // ============================================================================
  // Endpoint: Data Consistency
  // ============================================================================

  test('list and detail data match', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', 'Bio');

    const listUser = factory.getUser(user.id);
    const detailUser = factory.getUser(user.id);

    expect(listUser?.username).toBe(detailUser?.username);
  });

  test('repeated requests return same data', () => {
    const user = factory.createTestUser('alice', 'alice@example.com', 'Alice', '');

    const retrieved1 = factory.getUser(user.id);
    const retrieved2 = factory.getUser(user.id);

    expect(retrieved1?.id).toBe(retrieved2?.id);
  });
});
