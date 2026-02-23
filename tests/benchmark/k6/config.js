/**
 * VelocityBench k6 — Shared framework configuration
 *
 * Imported by smoke.js and full_suite.js to avoid duplication.
 * REST endpoints use base URL; GraphQL endpoints include the path.
 */

export const FRAMEWORK_URLS = {
  'fastapi-rest':   { type: 'rest',    url: 'http://localhost:8003' },
  'actix-web-rest': { type: 'rest',    url: 'http://localhost:8015' },
  'strawberry':     { type: 'graphql', url: 'http://localhost:8011/graphql' },
  'graphene':       { type: 'graphql', url: 'http://localhost:8002/graphql' },
  'go-gqlgen':      { type: 'graphql', url: 'http://localhost:4010/query' },
  'async-graphql':  { type: 'graphql', url: 'http://localhost:8016/' },
  'fraiseql-v':     { type: 'graphql', url: 'http://localhost:8815/graphql' },
  'fraiseql-tv':    { type: 'graphql', url: 'http://localhost:8816/graphql' },
};

export const ALICE_UUID = '11111111-1111-1111-1111-111111111111';

/**
 * GraphQL queries used by the benchmark suite.
 * Q1..Q3 match the same queries used in test_fraiseql_comparison.py for consistency.
 */
export const GQL_QUERIES = {
  Q1: '{ users(limit: 20) { id username fullName } }',
  Q2: '{ posts(limit: 10) { id title author { username fullName } } }',
  Q3: '{ comments(limit: 20) { id content author { username } post { title } } }',
  M1: `mutation { updateUser(id: "${ALICE_UUID}", bio: "bench-${Date.now()}") { id username bio } }`,
};

/**
 * REST equivalent paths (frameworks may not support all query shapes).
 */
export const REST_PATHS = {
  Q1: '/users?limit=20',
  Q2: '/posts?limit=10',
  Q3: '/comments?limit=20',
  M1: `/users/${ALICE_UUID}`,
};
