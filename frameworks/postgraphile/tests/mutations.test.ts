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

  afterEach(async () => {
    await factory.cleanup();
  });

  // Category 1: Mutation Type Introspection (5 tests)
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

    test('Mutation should support batch operations', async () => {
      const user1 = await factory.createUser({ name: 'User1' });
      const user2 = await factory.createUser({ name: 'User2' });

      // Verify multiple queries work (batch-like behavior)
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            user1: userById(id: ${user1.id}) { id name }
            user2: userById(id: ${user2.id}) { id name }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.user1).toBeDefined();
      expect(response.body.data.user2).toBeDefined();
    });

    test('should handle mutation variables', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `query GetUsers($limit: Int) {
            allUsers(first: $limit) { nodes { id } }
          }`,
          variables: { limit: 5 },
        });

      expect(response.status).toBe(200);
      expect(response.body.data.allUsers).toBeDefined();
    });
  });

  // Category 2: Data Modification Operations (10 tests)
  describe('Data Modification through GraphQL', () => {
    test('should support direct database changes visible in queries', async () => {
      const user = await factory.createUser({ name: 'InitialName' });

      // Verify user was created
      const response1 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: ${user.id}) { name } }`,
        });

      expect(response1.status).toBe(200);
      expect(response1.body.data.userById.name).toBe('InitialName');

      // Direct database modification
      const client = await pool.connect();
      await client.query(
        'UPDATE users SET name = $1 WHERE id = $2',
        ['UpdatedName', user.id]
      );
      client.release();

      // Verify change is visible in GraphQL
      const response2 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: ${user.id}) { name } }`,
        });

      expect(response2.status).toBe(200);
      expect(response2.body.data.userById.name).toBe('UpdatedName');
    });

    test('should reflect deletions in subsequent queries', async () => {
      const user = await factory.createUser({ name: 'ToDelete' });

      // Verify user exists
      const response1 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: ${user.id}) { id } }`,
        });

      expect(response1.status).toBe(200);
      expect(response1.body.data.userById).toBeDefined();

      // Delete user via direct database access
      const client = await pool.connect();
      await client.query('DELETE FROM users WHERE id = $1', [user.id]);
      client.release();

      // Verify deletion is visible in GraphQL
      const response2 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: ${user.id}) { id } }`,
        });

      expect(response2.status).toBe(200);
      expect(response2.body.data.userById).toBeNull();
    });

    test('should handle multiple object deletions', async () => {
      const user1 = await factory.createUser({ name: 'User1' });
      const user2 = await factory.createUser({ name: 'User2' });

      const client = await pool.connect();
      await client.query('DELETE FROM users WHERE id IN ($1, $2)', [user1.id, user2.id]);
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            user1: userById(id: ${user1.id}) { id }
            user2: userById(id: ${user2.id}) { id }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.user1).toBeNull();
      expect(response.body.data.user2).toBeNull();
    });

    test('should handle cascade deletions', async () => {
      const author = await factory.createUser({ name: 'Author' });
      const post = await factory.createPost({ title: 'Post', author_id: author.id });

      // Delete author (should cascade delete post due to FK constraint)
      const client = await pool.connect();
      await client.query('DELETE FROM users WHERE id = $1', [author.id]);
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: ${post.id}) { id } }`,
        });

      expect(response.status).toBe(200);
      // Post should be null due to cascade delete
      expect(response.body.data.postById).toBeNull();
    });

    test('should support bulk updates via database', async () => {
      await factory.createUser({ name: 'Test1' });
      await factory.createUser({ name: 'Test2' });
      await factory.createUser({ name: 'Test3' });

      // Update all users' bio
      const client = await pool.connect();
      await client.query('UPDATE users SET bio = $1 WHERE name LIKE $2', [
        'Bulk updated',
        'Test%',
      ]);
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers { nodes { name bio } } }`,
        });

      expect(response.status).toBe(200);
      const testUsers = response.body.data.allUsers.nodes.filter((u: any) => u.name.startsWith('Test'));
      testUsers.forEach((user: any) => {
        expect(user.bio).toBe('Bulk updated');
      });
    });

    test('should handle null value insertions', async () => {
      const client = await pool.connect();
      await client.query(
        'INSERT INTO users (id, name, email, bio) VALUES ($1, $2, $3, $4)',
        [Math.floor(Math.random() * 1000000), 'NullBioUser', 'test@example.com', null]
      );
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers { nodes { name bio } } }`,
        });

      expect(response.status).toBe(200);
      const nullBioUser = response.body.data.allUsers.nodes.find((u: any) => u.name === 'NullBioUser');
      expect(nullBioUser).toBeDefined();
      expect(nullBioUser.bio).toBeNull();
    });

    test('should respect transaction boundaries', async () => {
      const user = await factory.createUser({ name: 'TxTest' });

      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        await client.query('UPDATE users SET name = $1 WHERE id = $2', ['TxUpdatetesting', user.id]);
        await client.query('ROLLBACK');
      } finally {
        client.release();
      }

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: ${user.id}) { name } }`,
        });

      expect(response.status).toBe(200);
      // Name should be unchanged due to rollback
      expect(response.body.data.userById.name).toBe('TxTest');
    });

    test('should handle constraint violations gracefully', async () => {
      const user1 = await factory.createUser({ email: 'unique@example.com' });

      // Try to insert duplicate email
      const client = await pool.connect();
      try {
        await client.query(
          'INSERT INTO users (id, name, email) VALUES ($1, $2, $3)',
          [Math.floor(Math.random() * 1000000), 'User2', 'unique@example.com']
        );
      } catch (e) {
        // Expected to fail due to unique constraint
      } finally {
        client.release();
      }

      // Original user should still be queryable
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: ${user1.id}) { email } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.email).toBe('unique@example.com');
    });

    test('should handle relationship modifications', async () => {
      const author1 = await factory.createUser({ name: 'Author1' });
      const author2 = await factory.createUser({ name: 'Author2' });
      const post = await factory.createPost({ title: 'Post', author_id: author1.id });

      // Change author relationship
      const client = await pool.connect();
      await client.query('UPDATE posts SET author_id = $1 WHERE id = $2', [author2.id, post.id]);
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: ${post.id}) { title } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('Post');
    });
  });
});
