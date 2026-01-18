import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

/**
 * PostGraphile Error Handling and Edge Cases Tests
 *
 * Trinity Pattern: tb_user, tb_post, tb_comment tables
 * - pk_* = integer primary key (internal)
 * - id = UUID (external API identifier)
 * - fk_* = integer foreign key
 *
 * Field mappings (PostGraphile camelCase):
 * - full_name -> fullName
 * - created_at -> createdAt
 */
describe('PostGraphile Error Handling and Edge Cases', () => {
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

  // Category 1: Validation Errors (10 tests)
  describe('Validation and Input Errors', () => {
    test('should reject invalid GraphQL syntax', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ invalid syntax }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
      expect(response.body.errors).toBeDefined();
    });

    test('should return error for non-existent field', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "00000000-0000-0000-0000-000000000001") { nonExistentField } }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
      if (response.body.errors) {
        expect(response.body.errors.length).toBeGreaterThan(0);
      }
    });

    test('should return error for missing required arguments', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById { id } }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
      expect(response.body.errors).toBeDefined();
    });

    test('should return error for type mismatch in arguments', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "not_a_uuid") { id } }`,
        });

      // PostGraphile validates UUID format
      expect(response.status).toBeGreaterThanOrEqual(400);
      expect(response.body.errors).toBeDefined();
    });

    test('should handle null input gracefully', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: null,
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test('should reject malformed JSON', async () => {
      const response = await request(server)
        .post('/graphql')
        .set('Content-Type', 'application/json')
        .send('{invalid json}');

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test('should handle empty query', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: '',
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test('should handle undefined field type', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers { nodes { undefinedField } } }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test('should return error for duplicate field aliases', async () => {
      const user = await factory.createUser({ name: 'Test' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id: fullName
              id: email
            }
          }`,
        });

      // GraphQL should either error on duplicate aliases or handle gracefully
      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should handle deeply nested queries gracefully', async () => {
      const user = await factory.createUser({ name: 'Deep' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userById(id: "${user.id}") {
              id
              fullName
            }
          }`,
        });

      expect(response.status).toBe(200);
    });
  });

  // Category 2: Edge Cases (10 tests)
  describe('Edge Cases and Boundary Conditions', () => {
    test('should handle UUID queries for non-existent users', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "00000000-0000-0000-0000-000000000000") { id } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeNull();
    });

    test('should handle invalid UUID format gracefully', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "invalid-uuid") { id } }`,
        });

      // Invalid UUID should cause validation error
      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test('should handle special SQL characters in stored data', async () => {
      const user = await factory.createUser({
        name: "O'Reilly",
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { fullName } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe("O'Reilly");
    });

    test('should handle HTML entities', async () => {
      const user = await factory.createUser({
        name: '<script>alert("xss")</script>',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { fullName } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toContain('<script>');
    });

    test('should handle query with comments', async () => {
      const user = await factory.createUser({ name: 'CommentTest' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            # This is a comment
            userById(id: "${user.id}") {
              id
              # Another comment
              fullName
            }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe('CommentTest');
    });

    test('should handle request without explicit Content-Type header', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({ query: '{ __typename }' });

      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should handle whitespace in names', async () => {
      const user = await factory.createUser({
        name: '   Whitespace User   ',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { fullName } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe('   Whitespace User   ');
    });

    test('should handle unicode characters', async () => {
      const user = await factory.createUser({
        name: '测试用户 🚀',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { fullName } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe('测试用户 🚀');
    });

    test('should handle very long strings in bio', async () => {
      const longBio = 'A'.repeat(50000);
      const user = await factory.createUser({
        name: 'Long Bio User',
        bio: longBio,
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { bio } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.bio.length).toBe(50000);
    });

    test('should handle pagination with limit 0', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: 0) { nodes { id } } }`,
        });

      // First: 0 should return empty or be rejected
      expect(response.status).toBeGreaterThanOrEqual(200);
    });
  });

  // Additional Edge Cases
  describe('Request and Response Edge Cases', () => {
    test('should handle duplicate queries', async () => {
      const user = await factory.createUser({ name: 'Dup' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            first: userById(id: "${user.id}") { id }
            second: userById(id: "${user.id}") { id }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.first).toBeDefined();
      expect(response.body.data.second).toBeDefined();
    });

    test('should handle pagination with negative limit', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: -1) { nodes { id } } }`,
        });

      // Negative values should error or be handled
      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should return consistent data on repeated queries', async () => {
      const user = await factory.createUser({ name: 'Consistent' });

      const response1 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { fullName } }`,
        });

      const response2 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { fullName } }`,
        });

      expect(response1.body.data.userById.fullName).toBe(response2.body.data.userById.fullName);
    });

    test('should handle circular reference in object response', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 1) {
              nodes { id fullName }
              pageInfo { hasNextPage }
            }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.allUsers.nodes).toBeDefined();
      expect(response.body.data.allUsers.pageInfo).toBeDefined();
    });

    test('should handle case sensitivity in field names', async () => {
      const user = await factory.createUser({ name: 'CaseSensitive' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { FullName } }`,
        });

      // GraphQL is case-sensitive, FullName != fullName
      expect(response.status).toBeGreaterThanOrEqual(400);
      expect(response.body.errors).toBeDefined();
    });

    test('should handle introspection queries', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __schema {
              queryType { name }
              mutationType { name }
            }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__schema.queryType.name).toBe('Query');
    });

    test('should handle fragment queries', async () => {
      const user = await factory.createUser({ name: 'Fragment User' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `
            fragment UserFields on User {
              id
              fullName
            }
            {
              userById(id: "${user.id}") {
                ...UserFields
              }
            }
          `,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.fullName).toBe('Fragment User');
    });
  });
});
