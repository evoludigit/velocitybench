import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * PostGraphile GraphQL Mutation Tests
 *
 * Trinity Pattern: tb_user, tb_post, tb_comment tables
 * - pk_* = integer primary key (internal)
 * - id = UUID (external API identifier)
 * - fk_* = integer foreign key
 *
 * Field mappings (PostGraphile camelCase):
 * - full_name -> fullName
 * - created_at -> createdAt
 * - fk_author -> fkAuthor (exposed) + userByFkAuthor (relation)
 */
describe('PostGraphile GraphQL Mutations', () => {
  let server: any;
  let pool: Pool;
  let factory: TestFactory;

  beforeAll(async () => {
    server = await startServer();
    pool = new Pool({
      user: process.env.DB_USER || 'benchmark',
      password: process.env.DB_PASSWORD || 'benchmark123',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5434'),
      database: process.env.DB_NAME || 'velocitybench_benchmark',
    });
    factory = new TestFactory(pool);
  });

  afterAll(async () => {
    await pool.end();
    server.close();
  }, 15000);

  beforeEach(async () => {
    await factory.startTransaction();
  });

  afterEach(async () => {
    await factory.cleanup();
  });

  // Category 1: Mutation Type Introspection
  describe('Mutation Type Introspection', () => {
    test('should have Mutation type defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __type(name: "Mutation") { name kind } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type.name).toBe('Mutation');
      expect(response.body.data.__type.kind).toBe('OBJECT');
    });

    test('Mutation type should have fields', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __type(name: "Mutation") { fields { name } } }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      expect(Array.isArray(fields)).toBe(true);
      expect(fields.length).toBeGreaterThan(0);
    });

    test('Mutation fields should be properly typed', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Mutation") {
              fields {
                name
                type { kind name }
              }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      fields.forEach((field: any) => {
        expect(field.name).toBeDefined();
        expect(field.type).toBeDefined();
      });
    });
  });

  // Category 2: Data Visibility and Isolation
  describe('Data Visibility and Isolation', () => {
    test('should isolate data from different users', async () => {
      const user1 = await factory.createUser({ name: 'User One' });
      const user2 = await factory.createUser({ name: 'User Two' });

      // Query user1
      const response1 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user1.id}") { id username email fullName } }`,
        });

      expect(response1.status).toBe(200);
      expect(response1.body.data.userById.fullName).toBe('User One');

      // Query user2 separately
      const response2 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user2.id}") { id username email fullName } }`,
        });

      expect(response2.status).toBe(200);
      expect(response2.body.data.userById.fullName).toBe('User Two');
    });

    test('should handle multiple object queries in single request', async () => {
      const user1 = await factory.createUser({ name: 'Alice' });
      const user2 = await factory.createUser({ name: 'Bob' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            user1: userById(id: "${user1.id}") { id fullName }
            user2: userById(id: "${user2.id}") { id fullName }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.user1.fullName).toBe('Alice');
      expect(response.body.data.user2.fullName).toBe('Bob');
    });

    test('should support query variables', async () => {
      const user = await factory.createUser({ name: 'Variable User' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `query GetUser($userId: UUID!) {
            userById(id: $userId) { id fullName email }
          }`,
          variables: { userId: user.id },
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe('Variable User');
    });
  });

  // Category 3: Relationship Handling
  describe('Relationship Handling', () => {
    test('should properly handle post-author relationships', async () => {
      const author = await factory.createUser({ name: 'Post Author' });
      const post = await factory.createPost({ title: 'Test Post', fk_author: author.pk_user });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title userByFkAuthor { fullName } } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('Test Post');
      expect(response.body.data.postById.userByFkAuthor.fullName).toBe('Post Author');
    });

    test('should handle cascade deletions', async () => {
      const author = await factory.createUser({ name: 'Cascade Author' });
      const post = await factory.createPost({ title: 'ToDelete', fk_author: author.pk_user });
      const postId = post.id;

      // Delete author (should cascade delete post due to FK constraint)
      const client = await pool.connect();
      await client.query('DELETE FROM benchmark.tb_user WHERE id = $1', [author.id]);
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${postId}") { id } }`,
        });

      expect(response.status).toBe(200);
      // Post should be null due to cascade delete
      expect(response.body.data.postById).toBeNull();
    });

    test('should handle comment relationships', async () => {
      const user = await factory.createUser({ name: 'Comment Author' });
      const post = await factory.createPost({ title: 'CommentTest', fk_author: user.pk_user });
      const comment = await factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user, content: 'Nice post!' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ commentById(id: "${comment.id}") { id content userByFkAuthor { fullName } postByFkPost { title } } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.commentById).toBeDefined();
      expect(response.body.data.commentById.content).toBe('Nice post!');
      expect(response.body.data.commentById.userByFkAuthor.fullName).toBe('Comment Author');
      expect(response.body.data.commentById.postByFkPost.title).toBe('CommentTest');
    });
  });

  // Category 4: Constraint Validation
  describe('Constraint Validation', () => {
    test('should reject queries for non-existent objects', async () => {
      const fakeId = '550e8400-e29b-41d4-a716-446655440000';

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${fakeId}") { id fullName } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeNull();
    });

    test('should enforce unique constraints on email', async () => {
      // Create user with known email
      const uniqueEmail = `unique-${Date.now()}@example.com`;
      const user1 = await factory.createUser({ email: uniqueEmail, name: 'User1' });

      // Try to insert duplicate email via database
      const client = await pool.connect();
      try {
        await client.query(
          'INSERT INTO benchmark.tb_user (username, identifier, email, full_name) VALUES ($1, $2, $3, $4)',
          [`dup-user-${Date.now()}`, `dup-id-${Date.now()}`, uniqueEmail, 'User2']
        );
        // If we get here, the constraint wasn't enforced (bad!)
        expect(true).toBe(false);
      } catch (e: any) {
        // Expected to fail due to unique constraint
        expect(e.code).toBe('23505'); // unique_violation
      } finally {
        client.release();
      }

      // Original user should still be queryable
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user1.id}") { email } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.email).toBe(uniqueEmail);
    });

    test('should enforce unique constraints on username', async () => {
      // Create user with known username
      const uniqueUsername = `uniquename-${Date.now()}`;
      await factory.createUser({ username: uniqueUsername, name: 'User1' });

      // Try to insert duplicate username via database
      const client = await pool.connect();
      try {
        await client.query(
          'INSERT INTO benchmark.tb_user (username, identifier, email, full_name) VALUES ($1, $2, $3, $4)',
          [uniqueUsername, `dup-id-${Date.now()}`, `dup-email-${Date.now()}@example.com`, 'User2']
        );
        // If we get here, the constraint wasn't enforced (bad!)
        expect(true).toBe(false);
      } catch (e: any) {
        // Expected to fail due to unique constraint
        expect(e.code).toBe('23505'); // unique_violation
      } finally {
        client.release();
      }
    });
  });

  // Category 5: Null Handling
  describe('Null Handling', () => {
    test('should handle optional fields correctly', async () => {
      const user = await factory.createUser({
        name: 'Sparse User',
        bio: null,
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id fullName bio } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe('Sparse User');
      expect(response.body.data.userById.bio).toBeNull();
    });

    test('should handle post with content', async () => {
      const user = await factory.createUser({ name: 'Content Author' });
      const post = await factory.createPost({
        title: 'WithContent',
        content: 'This is the content',
        fk_author: user.pk_user,
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title content } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('WithContent');
      expect(response.body.data.postById.content).toBe('This is the content');
    });
  });
});
