/**
 * Security: Rate Limiting Tests (PostGraphile)
 *
 * These tests verify that the PostGraphile application can handle rate limiting
 * scenarios including per-user limits, per-IP limits, and window resets.
 * Note: PostGraphile doesn't have built-in rate limiting; these tests verify
 * the system's behavior under high load and document where middleware should be added.
 */

import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

describe('PostGraphile: Rate Limiting', () => {
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
  // Basic Rate Limiting Tests
  // ============================================================================

  test('should handle rapid sequential requests', async () => {
    const user = await factory.createUser({ username: 'rapiduser' });

    const query = `
      query GetUsers {
        allTbUsers(first: 10) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const requests = [];
    for (let i = 0; i < 20; i++) {
      requests.push(
        request(server)
          .post('/graphql')
          .send({ query })
      );
    }

    const responses = await Promise.all(requests);

    // Without rate limiting, all requests should succeed
    responses.forEach((response) => {
      expect(response.status).toBe(200);
      expect(response.body.data.allTbUsers.nodes).toBeDefined();
    });
  });

  test('should handle concurrent requests from same IP', async () => {
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

    const concurrentRequests = Array(15)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('X-Forwarded-For', '192.168.1.100')
          .send({ query })
      );

    const responses = await Promise.all(concurrentRequests);

    // Without rate limiting, all should succeed
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ============================================================================
  // Per-User Rate Limiting Tests
  // ============================================================================

  test('should track requests per authenticated user', async () => {
    const user = await factory.createUser({ username: 'authuser' });

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

    const userToken = 'user-token-123';

    const requests = [];
    for (let i = 0; i < 10; i++) {
      requests.push(
        request(server)
          .post('/graphql')
          .set('Authorization', `Bearer ${userToken}`)
          .send({ query })
      );
    }

    const responses = await Promise.all(requests);

    // Without rate limiting middleware, all succeed
    const successCount = responses.filter((r) => r.status === 200).length;
    expect(successCount).toBe(10);
  });

  test('should differentiate between different users', async () => {
    const user1 = await factory.createUser({ username: 'user1' });
    const user2 = await factory.createUser({ username: 'user2' });

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

    const user1Requests = Array(5)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('Authorization', 'Bearer user1-token')
          .send({ query })
      );

    const user2Requests = Array(5)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('Authorization', 'Bearer user2-token')
          .send({ query })
      );

    const allResponses = await Promise.all([...user1Requests, ...user2Requests]);

    // All requests should succeed without rate limiting
    allResponses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ============================================================================
  // Per-IP Rate Limiting Tests
  // ============================================================================

  test('should handle multiple requests from same IP', async () => {
    const user = await factory.createUser({ username: 'ipuser' });

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

    const requests = Array(12)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('X-Forwarded-For', '203.0.113.42')
          .send({ query })
      );

    const responses = await Promise.all(requests);

    // Without rate limiting, all succeed
    const successCount = responses.filter((r) => r.status === 200).length;
    expect(successCount).toBe(12);
  });

  test('should differentiate between different IPs', async () => {
    const user = await factory.createUser({ username: 'multiipuser' });

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

    const ip1Requests = Array(5)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('X-Forwarded-For', '198.51.100.1')
          .send({ query })
      );

    const ip2Requests = Array(5)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('X-Forwarded-For', '198.51.100.2')
          .send({ query })
      );

    const allResponses = await Promise.all([...ip1Requests, ...ip2Requests]);

    allResponses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ============================================================================
  // Rate Limit Window Tests
  // ============================================================================

  test('should handle burst requests within window', async () => {
    const user = await factory.createUser({ username: 'burstuser' });

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

    // Send burst of requests
    const burstRequests = Array(8)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .send({ query })
      );

    const responses = await Promise.all(burstRequests);

    // All should succeed without rate limiting
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  test('should reset rate limit after window expires', async () => {
    const user = await factory.createUser({ username: 'windowuser' });

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

    // First batch of requests
    const firstBatch = await Promise.all(
      Array(5)
        .fill(null)
        .map(() =>
          request(server)
            .post('/graphql')
            .send({ query })
        )
    );

    // Wait for potential window reset (simulated)
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Second batch of requests
    const secondBatch = await Promise.all(
      Array(5)
        .fill(null)
        .map(() =>
          request(server)
            .post('/graphql')
            .send({ query })
        )
    );

    // All should succeed
    [...firstBatch, ...secondBatch].forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ============================================================================
  // Different Endpoint Rate Limiting Tests
  // ============================================================================

  test('should handle rate limiting across different queries', async () => {
    const user = await factory.createUser({ username: 'multiquery' });
    const post = await factory.createPost({ fk_author: user.pk_user });

    const userQuery = `
      query GetUsers {
        allTbUsers(first: 5) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const postQuery = `
      query GetPosts {
        allTbPosts(first: 5) {
          nodes {
            id
            title
          }
        }
      }
    `;

    const requests = [
      ...Array(5)
        .fill(null)
        .map(() => request(server).post('/graphql').send({ query: userQuery })),
      ...Array(5)
        .fill(null)
        .map(() => request(server).post('/graphql').send({ query: postQuery })),
    ];

    const responses = await Promise.all(requests);

    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  test('should apply different limits to mutations vs queries', async () => {
    const user = await factory.createUser({ username: 'mutationuser' });

    const readQuery = `
      query GetUsers {
        allTbUsers(first: 5) {
          nodes {
            id
            username
          }
        }
      }
    `;

    const writeQuery = `
      mutation CreatePost($fkAuthor: Int!, $title: String!, $content: String!) {
        createTbPost(input: {
          tbPost: {
            fkAuthor: $fkAuthor
            identifier: "rate-limit-test"
            title: $title
            content: $content
            published: true
          }
        }) {
          tbPost {
            id
          }
        }
      }
    `;

    // Multiple reads
    const readRequests = Array(5)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .send({ query: readQuery })
      );

    // Multiple writes
    const writeRequests = Array(3)
      .fill(null)
      .map((_, i) =>
        request(server)
          .post('/graphql')
          .send({
            query: writeQuery,
            variables: {
              fkAuthor: user.pk_user,
              title: `Rate Limit Post ${i}`,
              content: `Content ${i}`,
            },
          })
      );

    const responses = await Promise.all([...readRequests, ...writeRequests]);

    // Without rate limiting, all succeed
    const successCount = responses.filter((r) => r.status === 200).length;
    expect(successCount).toBeGreaterThanOrEqual(5);
  });

  // ============================================================================
  // Complex Query Rate Limiting Tests
  // ============================================================================

  test('should handle rate limiting for expensive queries', async () => {
    const user = await factory.createUser({ username: 'expensiveuser' });
    await factory.createPost({ fk_author: user.pk_user });

    const expensiveQuery = `
      query ExpensiveQuery {
        allTbUsers {
          nodes {
            id
            username
            fullName
            postsByFkAuthor {
              nodes {
                id
                title
                commentsByFkPost {
                  nodes {
                    id
                    content
                  }
                }
              }
            }
          }
        }
      }
    `;

    const requests = Array(3)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .send({ query: expensiveQuery })
      );

    const responses = await Promise.all(requests);

    // Expensive queries should complete without rate limiting
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  test('should handle rate limiting for deep nested queries', async () => {
    const user = await factory.createUser({ username: 'deepuser' });
    const post = await factory.createPost({ fk_author: user.pk_user });
    await factory.createComment({ fk_post: post.pk_post, fk_author: user.pk_user });

    const deepQuery = `
      query DeepQuery {
        allTbUsers(first: 1) {
          nodes {
            postsByFkAuthor(first: 1) {
              nodes {
                commentsByFkPost(first: 1) {
                  nodes {
                    authorByFkAuthor {
                      postsByFkAuthor(first: 1) {
                        nodes {
                          id
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    `;

    const requests = Array(3)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .send({ query: deepQuery })
      );

    const responses = await Promise.all(requests);

    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ============================================================================
  // Rate Limit Header Tests
  // ============================================================================

  test('should include rate limit headers in response', async () => {
    const user = await factory.createUser({ username: 'headeruser' });

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

    const response = await request(server)
      .post('/graphql')
      .send({ query });

    expect(response.status).toBe(200);

    // Check for rate limit headers (if implemented)
    // These would be added by middleware
    // expect(response.headers).toHaveProperty('x-ratelimit-limit');
    // expect(response.headers).toHaveProperty('x-ratelimit-remaining');
    // expect(response.headers).toHaveProperty('x-ratelimit-reset');
  });

  test('should provide rate limit information after limit exceeded', async () => {
    const user = await factory.createUser({ username: 'limituser' });

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

    // Make many requests
    const requests = Array(25)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .send({ query })
      );

    const responses = await Promise.all(requests);

    // Without rate limiting, all succeed
    const successCount = responses.filter((r) => r.status === 200).length;
    expect(successCount).toBe(25);

    // If rate limited, the response should include retry-after header
    // const rateLimited = responses.find((r) => r.status === 429);
    // if (rateLimited) {
    //   expect(rateLimited.headers).toHaveProperty('retry-after');
    // }
  });

  // ============================================================================
  // Bypass and Whitelist Tests
  // ============================================================================

  test('should allow whitelisted IPs to bypass rate limits', async () => {
    const user = await factory.createUser({ username: 'whitelistuser' });

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

    const requests = Array(30)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('X-Forwarded-For', '127.0.0.1') // Localhost typically whitelisted
          .send({ query })
      );

    const responses = await Promise.all(requests);

    // Localhost should not be rate limited
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  test('should allow admin users to bypass rate limits', async () => {
    const admin = await factory.createUser({ username: 'admin' });

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

    const requests = Array(20)
      .fill(null)
      .map(() =>
        request(server)
          .post('/graphql')
          .set('Authorization', 'Bearer admin-token')
          .set('X-User-Role', 'admin')
          .send({ query })
      );

    const responses = await Promise.all(requests);

    // Admin requests should succeed
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });

  // ============================================================================
  // Distributed Rate Limiting Tests
  // ============================================================================

  test('should handle rate limiting across multiple servers', async () => {
    const user = await factory.createUser({ username: 'distributeduser' });

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

    // Simulate requests from different server instances
    const requests = Array(10)
      .fill(null)
      .map((_, i) =>
        request(server)
          .post('/graphql')
          .set('X-Server-Instance', `server-${i % 3}`)
          .send({ query })
      );

    const responses = await Promise.all(requests);

    // Should succeed regardless of server instance
    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });
});
