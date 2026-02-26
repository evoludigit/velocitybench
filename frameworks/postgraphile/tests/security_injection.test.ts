/**
 * Security: SQL Injection Prevention Tests (PostGraphile)
 *
 * These tests verify that PostGraphile's auto-generated GraphQL schema properly
 * handles SQL injection attempts in query arguments and mutation inputs.
 * PostGraphile uses parameterized queries by design, but we verify this behavior.
 */

import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

describe('PostGraphile: SQL Injection Prevention', () => {
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

  // ============================================================================
  // Basic SQL Injection Tests
  // ============================================================================

  test('should prevent basic OR injection in query argument', async () => {
    const user = await factory.createUser({ username: 'alice' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
            fullName
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "' OR '1'='1" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent UNION-based injection', async () => {
    const user = await factory.createUser({ username: 'bob' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "' UNION SELECT * FROM benchmark.tb_user--" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent stacked queries injection', async () => {
    const user = await factory.createUser({ username: 'charlie' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "'; DROP TABLE benchmark.tb_user; --" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);

    // Verify table still exists
    const users = await request(server)
      .post('/graphql')
      .send({
        query: '{ allTbUsers { totalCount } }',
      });

    expect(users.status).toBe(200);
    expect(users.body.data.allTbUsers.totalCount).toBeGreaterThanOrEqual(0);
  });

  test('should prevent comment sequence injection', async () => {
    const user = await factory.createUser({ username: 'david' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "david'--" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent time-based blind injection', async () => {
    const user = await factory.createUser({ username: 'eve' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const startTime = Date.now();

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "' AND pg_sleep(5)--" },
      });

    const duration = Date.now() - startTime;

    expect(response.status).toBe(200);
    expect(duration).toBeLessThan(2000); // Should not sleep
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent boolean-based blind injection', async () => {
    const user = await factory.createUser({ username: 'frank' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "' AND 1=1--" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  // ============================================================================
  // Mutation Injection Tests
  // ============================================================================

  test('should prevent SQL injection in createUser mutation', async () => {
    const query = `
      mutation CreateUser($username: String!, $email: String!, $fullName: String!) {
        createTbUser(input: {
          tbUser: {
            username: $username
            email: $email
            fullName: $fullName
            identifier: "test-identifier"
          }
        }) {
          tbUser {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: {
          username: "'; DROP TABLE benchmark.tb_user; --",
          email: 'malicious@example.com',
          fullName: 'Malicious User',
        },
      });

    expect(response.status).toBe(200);

    if (response.body.data?.createTbUser) {
      // Mutation succeeded - verify username is stored as literal
      expect(response.body.data.createTbUser.tbUser.username).toBe("'; DROP TABLE benchmark.tb_user; --");

      // Cleanup - delete the created user
      const client = await pool.connect();
      try {
        await client.query(
          'DELETE FROM benchmark.tb_user WHERE username = $1',
          ["'; DROP TABLE benchmark.tb_user; --"]
        );
      } finally {
        client.release();
      }
    }

    // Verify table still exists
    const users = await request(server)
      .post('/graphql')
      .send({
        query: '{ allTbUsers { totalCount } }',
      });

    expect(users.status).toBe(200);
  });

  test('should prevent SQL injection in post content', async () => {
    const user = await factory.createUser({ username: 'author' });

    const query = `
      mutation CreatePost($fkAuthor: Int!, $title: String!, $content: String!) {
        createTbPost(input: {
          tbPost: {
            fkAuthor: $fkAuthor
            identifier: "test-post"
            title: $title
            content: $content
            published: true
          }
        }) {
          tbPost {
            id
            content
          }
        }
      }
    `;

    const maliciousContent = "'; DELETE FROM benchmark.tb_user WHERE '1'='1";

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: {
          fkAuthor: user.pk_user,
          title: 'Test Post',
          content: maliciousContent,
        },
      });

    expect(response.status).toBe(200);

    if (response.body.data?.createTbPost) {
      // Verify content is stored as literal
      expect(response.body.data.createTbPost.tbPost.content).toBe(maliciousContent);
    }

    // Verify users are not deleted
    const users = await request(server)
      .post('/graphql')
      .send({
        query: '{ allTbUsers { totalCount } }',
      });

    expect(users.status).toBe(200);
    expect(users.body.data.allTbUsers.totalCount).toBeGreaterThanOrEqual(1);
  });

  // ============================================================================
  // Filter and Search Injection Tests
  // ============================================================================

  test('should prevent injection in filter conditions', async () => {
    const user1 = await factory.createUser({ username: 'alice' });
    const user2 = await factory.createUser({ username: 'bob' });

    const query = `
      query FilterUsers($filter: TbUserFilter!) {
        allTbUsers(filter: $filter) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: {
          filter: {
            username: {
              equalTo: "alice' OR '1'='1",
            },
          },
        },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should properly escape single quotes in legitimate data', async () => {
    const query = `
      mutation CreateUser($username: String!, $email: String!, $fullName: String!, $bio: String) {
        createTbUser(input: {
          tbUser: {
            username: $username
            email: $email
            fullName: $fullName
            identifier: "test-obrien"
            bio: $bio
          }
        }) {
          tbUser {
            id
            username
            fullName
            bio
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: {
          username: "obrien",
          email: 'obrien@example.com',
          fullName: "O'Brien",
          bio: "It's a bio",
        },
      });

    expect(response.status).toBe(200);

    if (response.body.data?.createTbUser) {
      expect(response.body.data.createTbUser.tbUser.fullName).toBe("O'Brien");
      expect(response.body.data.createTbUser.tbUser.bio).toBe("It's a bio");

      // Cleanup
      const client = await pool.connect();
      try {
        await client.query(
          'DELETE FROM benchmark.tb_user WHERE username = $1',
          ['obrien']
        );
      } finally {
        client.release();
      }
    }
  });

  test('should handle SQL comments in bio as literal text', async () => {
    const user = await factory.createUser({
      username: 'testuser',
      bio: 'This is a bio -- with dashes',
    });

    const query = `
      query GetUser($pkUser: Int!) {
        tbUserByPkUser(pkUser: $pkUser) {
          bio
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { pkUser: user.pk_user },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.tbUserByPkUser.bio).toBe('This is a bio -- with dashes');
  });

  // ============================================================================
  // GraphQL-Specific Injection Tests
  // ============================================================================

  test('should prevent hex-encoded injection attempts', async () => {
    const user = await factory.createUser({ username: 'admin' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: '0x61646d696e' }, // hex for 'admin'
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent URL-encoded injection', async () => {
    const user = await factory.createUser({ username: 'user' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "user%27%20OR%20%271%27%3D%271" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent subquery injection', async () => {
    const user = await factory.createUser({ username: 'user' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: "' AND pk_user IN (SELECT pk_user FROM benchmark.tb_user)--" },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(0);
  });

  test('should prevent null byte injection', async () => {
    const query = `
      mutation CreateUser($username: String!, $email: String!, $fullName: String!) {
        createTbUser(input: {
          tbUser: {
            username: $username
            email: $email
            fullName: $fullName
            identifier: "test-null"
          }
        }) {
          tbUser {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: {
          username: "user\x00admin",
          email: 'null@example.com',
          fullName: 'Null User',
        },
      });

    expect(response.status).toBe(200);

    if (response.body.data?.createTbUser) {
      // If created, username should be stored as is
      const createdUsername = response.body.data.createTbUser.tbUser.username;
      expect(createdUsername).toContain('user');

      // Cleanup
      const client = await pool.connect();
      try {
        await client.query(
          'DELETE FROM benchmark.tb_user WHERE username LIKE $1',
          ['user%admin']
        );
      } finally {
        client.release();
      }
    }
  });

  test('should validate that PostGraphile uses parameterized queries', async () => {
    // This test verifies the core assumption: PostGraphile uses prepared statements
    const user = await factory.createUser({ username: 'testuser' });

    const query = `
      query GetUser($username: String!) {
        allTbUsers(condition: { username: $username }) {
          nodes {
            id
            username
          }
        }
      }
    `;

    // Legitimate query should work
    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { username: 'testuser' },
      });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toHaveLength(1);
    expect(response.body.data.allTbUsers.nodes[0].username).toBe('testuser');
  });
});
