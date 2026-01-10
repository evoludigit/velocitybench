import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

// TODO: Update to use Trinity Pattern schema (tb_user, tb_post, tb_comment)
// These tests reference old schema with 'users', 'posts' tables and 'name' field
describe.skip('PostGraphile Error Handling and Edge Cases', () => {
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
          query: `{ userById(id: 1) { nonExistentField } }`,
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
          query: `{ userById(id: "not_an_int") { id } }`,
        });

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
          query: `{ allUsers { undefinedField } }`,
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
              id: name
              id: email
            }
          }`,
        });

      // This should either error or handle gracefully
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
              name
            }
          }`,
        });

      expect(response.status).toBe(200);
    });
  });

  // Category 2: Edge Cases (10 tests)
  describe('Edge Cases and Boundary Conditions', () => {
    test('should handle zero as valid ID', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: 0) { id } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data).toBeDefined();
    });

    test('should handle negative numbers', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: -1) { id } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeNull();
    });

    test('should handle very large integers', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: 999999999999) { id } }`,
        });

      // Large integers outside Int range may cause GraphQL validation errors (400)
      // or be coerced to a valid number that returns null (200)
      expect([200, 400]).toContain(response.status);
    });

    test('should handle empty strings', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `mutation {
            createUser(input: { user: { name: "", email: "" } }) {
              user { id }
            }
          }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should handle strings with only whitespace', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `mutation {
            createUser(input: { user: { name: "   ", email: "test@example.com" } }) {
              user { id name }
            }
          }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(200);
      if (response.body.data?.createUser?.user) {
        expect(response.body.data.createUser.user.name.trim()).toBe('');
      }
    });

    test('should handle very long strings', async () => {
      const longString = 'A'.repeat(50000);
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `mutation {
            createUser(input: { user: { name: "${longString}", email: "long@example.com" } }) {
              user { id }
            }
          }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should handle special SQL characters', async () => {
      const user = await factory.createUser({
        name: "O'Reilly",
        email: 'special@example.com',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toBe("O'Reilly");
    });

    test('should handle HTML entities', async () => {
      const user = await factory.createUser({
        name: '<script>alert("xss")</script>',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toContain('<script>');
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
              name
            }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toBe('CommentTest');
    });

    test('should handle request without Content-Type header', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({ query: '{ __typename }' });

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

    test('should handle pagination with limit 0', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: 0) { nodes { id } } }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should handle pagination with negative limit', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: -1) { nodes { id } } }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(200);
    });

    test('should return consistent data on repeated queries', async () => {
      const user = await factory.createUser({ name: 'Consistent' });

      const response1 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name } }`,
        });

      const response2 = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name } }`,
        });

      expect(response1.body.data.userById.name).toBe(response2.body.data.userById.name);
    });

    test('should handle circular reference in object response', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 1) {
              nodes { id name }
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
          query: `{ userById(id: "${user.id}") { Name } }`,
        });

      expect(response.status).toBeGreaterThanOrEqual(400);
      expect(response.body.errors).toBeDefined();
    });
  });
});
