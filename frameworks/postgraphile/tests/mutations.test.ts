import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

describe('PostGraphile GraphQL Mutations', () => {
  let server: any;
  let pool: Pool;
  let factory: TestFactory;

  beforeAll(async () => {
    server = await startServer();
    pool = new Pool({
      user: process.env.DB_USER || 'velocitybench',
      password: process.env.DB_PASSWORD || 'password',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME || 'velocitybench_test',
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
      const user1 = await factory.createUser({ username: 'user1', email: 'user1@example.com' });
      const user2 = await factory.createUser({ username: 'user2', email: 'user2@example.com' });

      // Query user1
      const response1 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user1.id}") { id username email } }`,
        });

      expect(response1.status).toBe(200);
      expect(response1.body.data.userById.username).toBe('user1');
      expect(response1.body.data.userById.email).toBe('user1@example.com');

      // Query user2 separately
      const response2 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user2.id}") { id username email } }`,
        });

      expect(response2.status).toBe(200);
      expect(response2.body.data.userById.username).toBe('user2');
      expect(response2.body.data.userById.email).toBe('user2@example.com');
    });

    test('should handle multiple object queries in single request', async () => {
      const user1 = await factory.createUser({ username: 'alice', email: 'alice@example.com' });
      const user2 = await factory.createUser({ username: 'bob', email: 'bob@example.com' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            user1: userById(id: "${user1.id}") { id username }
            user2: userById(id: "${user2.id}") { id username }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.user1.username).toBe('alice');
      expect(response.body.data.user2.username).toBe('bob');
    });

    test('should support query variables', async () => {
      const user = await factory.createUser({ username: 'testuser', email: 'test@example.com' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `query GetUser($userId: UUID!) {
            userById(id: $userId) { id username email }
          }`,
          variables: { userId: user.id },
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.username).toBe('testuser');
    });
  });

  // Category 3: Relationship Handling
  describe('Relationship Handling', () => {
    test('should properly handle post-author relationships', async () => {
      const author = await factory.createUser({ username: 'author1', email: 'author@example.com' });
      const post = await factory.createPost({ title: 'Test Post', fk_author: author.pk_user });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('Test Post');
    });

    test('should handle cascade deletions', async () => {
      const author = await factory.createUser({ username: 'author2', email: 'author2@example.com' });
      const post = await factory.createPost({ title: 'ToDelete', fk_author: author.pk_user });

      // Delete author (should cascade delete post due to FK constraint)
      const client = await pool.connect();
      await client.query('DELETE FROM benchmark.tb_user WHERE id = $1', [author.id]);
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id } }`,
        });

      expect(response.status).toBe(200);
      // Post should be null due to cascade delete
      expect(response.body.data.postById).toBeNull();
    });

    test('should handle null relationships', async () => {
      // Test with comment that has no parent
      const user = await factory.createUser({ username: 'commenter', email: 'comment@example.com' });
      const post = await factory.createPost({ title: 'CommentTest', fk_author: user.pk_user });
      const comment = await factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ commentById(id: "${comment.id}") { id content isApproved } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.commentById).toBeDefined();
      expect(response.body.data.commentById.content).toBe('Test comment');
    });
  });

  // Category 4: Constraint Validation
  describe('Constraint Validation', () => {
    test('should reject queries for non-existent objects', async () => {
      const fakeId = '550e8400-e29b-41d4-a716-446655440000';

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${fakeId}") { id username } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeNull();
    });

    test('should enforce unique constraints on email', async () => {
      const user1 = await factory.createUser({ username: 'user1', email: 'unique@example.com' });

      // Try to insert duplicate email via database
      const client = await pool.connect();
      try {
        await client.query(
          'INSERT INTO benchmark.tb_user (username, email) VALUES ($1, $2)',
          ['user2', 'unique@example.com']
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
      expect(response.body.data.userById.email).toBe('unique@example.com');
    });

    test('should enforce unique constraints on username', async () => {
      const user1 = await factory.createUser({ username: 'uniquename', email: 'email1@example.com' });

      // Try to insert duplicate username via database
      const client = await pool.connect();
      try {
        await client.query(
          'INSERT INTO benchmark.tb_user (username, email) VALUES ($1, $2)',
          ['uniquename', 'email2@example.com']
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
        username: 'sparse',
        email: 'sparse@example.com',
        first_name: undefined,
        last_name: undefined,
        bio: null,
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id username firstName lastName bio } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.username).toBe('sparse');
      expect(response.body.data.userById.firstName).toBeNull();
      expect(response.body.data.userById.lastName).toBeNull();
      expect(response.body.data.userById.bio).toBeNull();
    });

    test('should handle null post content', async () => {
      const user = await factory.createUser({ username: 'postauthor', email: 'post@example.com' });
      const post = await factory.createPost({
        title: 'NoContent',
        content: null,
        fk_author: user.pk_user,
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title content } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('NoContent');
      expect(response.body.data.postById.content).toBeNull();
    });
  });
});
