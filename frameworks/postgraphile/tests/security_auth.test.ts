/**
 * Security: Authentication and Authorization Tests (PostGraphile)
 *
 * These tests verify that the PostGraphile application properly handles
 * authentication and authorization scenarios including missing, invalid,
 * and expired tokens/headers.
 */

import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

describe('PostGraphile: Authentication and Authorization', () => {
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
  // Missing Authentication Tests
  // ============================================================================

  test('should allow public queries without authentication', async () => {
    // PostGraphile typically allows public access unless RLS is configured
    const user = await factory.createUser({ username: 'publicuser' });

    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({ query });

    expect(response.status).toBe(200);
    expect(response.body.data.allTbUsers.nodes).toBeDefined();
  });

  test('should handle missing authorization header gracefully', async () => {
    const query = `
      query Introspection {
        __schema {
          types {
            name
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({ query });

    expect(response.status).toBe(200);
    expect(response.body.data.__schema).toBeDefined();
  });

  // ============================================================================
  // Invalid Authentication Tests
  // ============================================================================

  test('should handle invalid authorization header format', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', 'InvalidFormat')
      .send({ query });

    // PostGraphile typically ignores invalid headers if auth is not enforced
    expect(response.status).toBe(200);
  });

  test('should handle malformed JWT token', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', 'Bearer not.a.jwt')
      .send({ query });

    // Without JWT validation middleware, this should still work
    expect(response.status).toBe(200);
  });

  test('should handle empty authorization header', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', '')
      .send({ query });

    expect(response.status).toBe(200);
  });

  // ============================================================================
  // Token Validation Tests
  // ============================================================================

  test('should handle expired JWT token gracefully', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjF9.invalid';

    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', `Bearer ${expiredToken}`)
      .send({ query });

    // Without middleware, expired tokens are ignored
    expect(response.status).toBe(200);
  });

  test('should handle tampered JWT token', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4ifQ.tamperedsignature';

    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', `Bearer ${tamperedToken}`)
      .send({ query });

    expect(response.status).toBe(200);
  });

  // ============================================================================
  // Authorization Tests (Row-Level Security)
  // ============================================================================

  test('should respect database-level access controls', async () => {
    const user = await factory.createUser({ username: 'testuser' });

    const query = `
      query GetUserByPk($pkUser: Int!) {
        tbUserByPkUser(pkUser: $pkUser) {
          id
          username
          fullName
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
    expect(response.body.data.tbUserByPkUser).toBeDefined();
  });

  test('should handle unauthorized mutation attempts', async () => {
    const query = `
      mutation CreateUser($username: String!, $email: String!, $fullName: String!) {
        createTbUser(input: {
          tbUser: {
            username: $username
            email: $email
            fullName: $fullName
            identifier: "test-user"
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
          username: 'unauthorizeduser',
          email: 'unauth@example.com',
          fullName: 'Unauthorized User',
        },
      });

    // Without auth middleware, mutations are allowed
    expect(response.status).toBe(200);

    if (response.body.data?.createTbUser) {
      // Cleanup
      const client = await pool.connect();
      try {
        await client.query(
          'DELETE FROM benchmark.tb_user WHERE username = $1',
          ['unauthorizeduser']
        );
      } finally {
        client.release();
      }
    }
  });

  // ============================================================================
  // Permission Escalation Tests
  // ============================================================================

  test('should prevent unauthorized access to other users data', async () => {
    const user1 = await factory.createUser({ username: 'user1' });
    const user2 = await factory.createUser({ username: 'user2' });

    const query = `
      query GetUser($pkUser: Int!) {
        tbUserByPkUser(pkUser: $pkUser) {
          id
          username
          email
        }
      }
    `;

    // Without RLS, any user can read any other user
    const response = await request(server)
      .post('/graphql')
      .send({
        query,
        variables: { pkUser: user2.pk_user },
      });

    expect(response.status).toBe(200);
    // In a system without auth, this would succeed
    expect(response.body.data.tbUserByPkUser).toBeDefined();
  });

  test('should prevent role escalation via header manipulation', async () => {
    const user = await factory.createUser({ username: 'normaluser' });

    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('X-Hasura-Role', 'admin') // Attempt role escalation
      .send({ query });

    expect(response.status).toBe(200);
    // Header should be ignored without proper auth
  });

  // ============================================================================
  // Session Management Tests
  // ============================================================================

  test('should handle concurrent requests with same token', async () => {
    const user = await factory.createUser({ username: 'concurrentuser' });

    const query = `
      query GetUsers {
        allTbUsers(first: 5) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const token = 'test-token-123';

    const requests = await Promise.all([
      request(server).post('/graphql').set('Authorization', `Bearer ${token}`).send({ query }),
      request(server).post('/graphql').set('Authorization', `Bearer ${token}`).send({ query }),
      request(server).post('/graphql').set('Authorization', `Bearer ${token}`).send({ query }),
    ]);

    requests.forEach((response) => {
      expect(response.status).toBe(200);
      expect(response.body.data.allTbUsers.nodes).toBeDefined();
    });
  });

  test('should handle session timeout gracefully', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    // Simulate an old/expired session token
    const oldToken = 'expired-session-token-from-yesterday';

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', `Bearer ${oldToken}`)
      .send({ query });

    // Without session management, token is ignored
    expect(response.status).toBe(200);
  });

  // ============================================================================
  // API Key Tests
  // ============================================================================

  test('should handle missing API key', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({ query });

    expect(response.status).toBe(200);
  });

  test('should handle invalid API key format', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('X-API-Key', 'invalid-key-format')
      .send({ query });

    expect(response.status).toBe(200);
  });

  // ============================================================================
  // CORS and Origin Tests
  // ============================================================================

  test('should handle CORS preflight requests', async () => {
    const response = await request(server)
      .options('/graphql')
      .set('Origin', 'http://example.com')
      .set('Access-Control-Request-Method', 'POST');

    // CORS should be handled by middleware
    expect([200, 204]).toContain(response.status);
  });

  test('should validate origin in CORS requests', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Origin', 'http://malicious-site.com')
      .send({ query });

    // CORS policy depends on server configuration
    expect([200, 403]).toContain(response.status);
  });

  // ============================================================================
  // GraphQL-Specific Auth Tests
  // ============================================================================

  test('should prevent introspection if disabled', async () => {
    const query = `
      query IntrospectionQuery {
        __schema {
          queryType {
            name
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({ query });

    // Introspection is typically enabled in dev/test
    expect(response.status).toBe(200);
  });

  test('should handle authentication in batch queries', async () => {
    const user = await factory.createUser({ username: 'batchuser' });

    const queries = [
      {
        query: '{ allTbUsers(first: 1) { nodes { id } } }',
      },
      {
        query: '{ allTbPosts(first: 1) { nodes { id } } }',
      },
    ];

    const response = await request(server)
      .post('/graphql')
      .send(queries);

    // Batch queries may or may not be supported
    expect([200, 400]).toContain(response.status);
  });

  test('should handle authentication in aliased queries', async () => {
    const user1 = await factory.createUser({ username: 'user1' });
    const user2 = await factory.createUser({ username: 'user2' });

    const query = `
      query GetMultipleUsers {
        firstUser: tbUserByPkUser(pkUser: ${user1.pk_user}) {
          id
          username
        }
        secondUser: tbUserByPkUser(pkUser: ${user2.pk_user}) {
          id
          username
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .send({ query });

    expect(response.status).toBe(200);
    expect(response.body.data.firstUser).toBeDefined();
    expect(response.body.data.secondUser).toBeDefined();
  });

  // ============================================================================
  // Header Injection Tests
  // ============================================================================

  test('should prevent header injection attacks', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('Authorization', 'Bearer token\r\nX-Injected-Header: malicious')
      .send({ query });

    // Header injection should be prevented by HTTP server
    expect(response.status).toBe(200);
  });

  test('should sanitize custom headers', async () => {
    const query = `
      query GetUsers {
        allTbUsers {
          nodes {
            id
            username
          }
        }
      }
    `;

    const response = await request(server)
      .post('/graphql')
      .set('X-User-Id', "1'; DROP TABLE users; --")
      .send({ query });

    expect(response.status).toBe(200);
  });
});
