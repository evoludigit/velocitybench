import { createServer, Server } from 'node:http';
import request from 'supertest';

/**
 * Smoke test against the real v5 server wired to the benchmark database.
 *
 * Uses the same env defaults as src/graphile.config.ts (set DB_PORT=5434 when
 * postgres runs via the root docker-compose port mapping).
 */
import { startServer } from '../src/index';

let server: Server;

beforeAll(async () => {
  server = (await startServer()) as Server;
});

afterAll(() => {
  server.close();
});

test('health endpoint reports healthy and the postgraphile version', async () => {
  const response = await request(server).get('/health');
  expect(response.status).toBe(200);
  expect(response.body.status).toBe('healthy');
  expect(response.body.version).toMatch(/^5\./);
});

test('Q1 benchmark document returns users with uuid ids', async () => {
  const response = await request(server)
    .post('/graphql')
    .send({
      query: '{ allTbUsers(first: 20) { nodes { id: rowId username fullName } } }',
    });
  expect(response.status).toBe(200);
  expect(response.body.errors).toBeUndefined();
  const nodes = response.body.data.allTbUsers.nodes;
  expect(nodes).toHaveLength(20);
  expect(nodes[0].id).toMatch(
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
  );
});

test('Q2b nesting resolves the author relation', async () => {
  const response = await request(server)
    .post('/graphql')
    .send({
      query:
        '{ allTbPosts(first: 10) { nodes { id: rowId title tbUserByFkAuthor { username fullName } } } }',
    });
  expect(response.status).toBe(200);
  expect(response.body.errors).toBeUndefined();
  const nodes = response.body.data.allTbPosts.nodes;
  expect(nodes.length).toBeGreaterThan(0);
  expect(nodes[0].tbUserByFkAuthor.username).toBeTruthy();
});
