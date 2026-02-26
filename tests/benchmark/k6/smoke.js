/**
 * VelocityBench k6 — Smoke test
 *
 * Quick connectivity check: 1 VU, 5 iterations, users query.
 * Verifies the target framework is reachable and returns valid data.
 *
 * Usage:
 *   k6 run --env FRAMEWORK=strawberry benchmarks/k6/smoke.js
 *   k6 run --env FRAMEWORK=go-gqlgen  benchmarks/k6/smoke.js
 *
 * If FRAMEWORK is unset, defaults to strawberry.
 */

import http from 'k6/http';
import { check, fail } from 'k6';
import { FRAMEWORK_URLS, GQL_QUERIES, REST_PATHS } from './config.js';

const FRAMEWORK = __ENV.FRAMEWORK || 'strawberry';
const CONFIG = FRAMEWORK_URLS[FRAMEWORK];

if (!CONFIG) {
  fail(`Unknown framework: "${FRAMEWORK}". Valid values: ${Object.keys(FRAMEWORK_URLS).join(', ')}`);
}

export const options = {
  vus: 1,
  iterations: 5,
  thresholds: {
    'http_req_failed': ['rate==0'],
    'http_req_duration': ['p(99)<5000'],
  },
};

export default function () {
  if (CONFIG.type === 'graphql') {
    const payload = JSON.stringify({ query: GQL_QUERIES.Q1 });
    const res = http.post(CONFIG.url, payload, {
      headers: { 'Content-Type': 'application/json' },
    });

    check(res, {
      'HTTP 200': (r) => r.status === 200,
      'has data key': (r) => {
        try { return JSON.parse(r.body).data !== undefined; } catch { return false; }
      },
      'no errors': (r) => {
        try {
          const body = JSON.parse(r.body);
          return !body.errors || body.errors.length === 0;
        } catch { return false; }
      },
      'users array non-empty': (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body.data?.users) && body.data.users.length > 0;
        } catch { return false; }
      },
    });
  } else {
    // REST
    const res = http.get(`${CONFIG.url}${REST_PATHS.Q1}`);
    check(res, {
      'HTTP 200': (r) => r.status === 200,
      'body non-empty': (r) => r.body && r.body.length > 2,
    });
  }
}
