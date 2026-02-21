/**
 * VelocityBench k6 — Full Benchmark Suite
 *
 * Stages:
 *   0:00 –  0:30  Warmup     ( 10 VUs)
 *   0:30 –  2:30  Ramp-up    ( 10 → 100 VUs)
 *   2:30 –  7:30  Sustained  (100 VUs, 5 minutes)
 *   7:30 –  8:00  Cooldown   (100 → 0 VUs)
 *
 * Request mix (realistic production approximation):
 *   60%  Q1  users(limit:20)  — flat list, no nesting
 *   20%  Q2  posts+author     — one-level nesting
 *   15%  Q3  comments+author+post — two-level nesting (CQRS stress test)
 *    5%  M1  updateUser mutation — write traffic
 *
 * Usage:
 *   k6 run --env FRAMEWORK=strawberry benchmarks/k6/full_suite.js
 *   k6 run --env FRAMEWORK=fraiseql-tv \
 *       --out json=reports/k6-fraiseql-tv.json \
 *       benchmarks/k6/full_suite.js
 *
 * Thresholds (applied globally):
 *   http_req_failed  < 1%     (hard gate — fail run if exceeded)
 *   http_req_duration p99 < 2s
 *   q3_duration_ms   p99 < 5s (relaxed for Python frameworks)
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { FRAMEWORK_URLS, GQL_QUERIES, REST_PATHS, ALICE_UUID } from './config.js';

// ---------------------------------------------------------------------------
// Framework selection
// ---------------------------------------------------------------------------

const FRAMEWORK = __ENV.FRAMEWORK || 'strawberry';
const CONFIG = FRAMEWORK_URLS[FRAMEWORK];

if (!CONFIG) {
  throw new Error(
    `Unknown framework: "${FRAMEWORK}". ` +
    `Valid values: ${Object.keys(FRAMEWORK_URLS).join(', ')}`
  );
}

// ---------------------------------------------------------------------------
// Custom per-query metrics
// ---------------------------------------------------------------------------

const errorRate     = new Rate('errors');
const q1Duration    = new Trend('q1_duration_ms',  true);
const q2Duration    = new Trend('q2_duration_ms',  true);
const q3Duration    = new Trend('q3_duration_ms',  true);
const m1Duration    = new Trend('m1_duration_ms',  true);
const q1Requests    = new Counter('q1_requests');
const q2Requests    = new Counter('q2_requests');
const q3Requests    = new Counter('q3_requests');
const m1Requests    = new Counter('m1_requests');

// ---------------------------------------------------------------------------
// Stage configuration
// ---------------------------------------------------------------------------

export const options = {
  stages: [
    { duration: '30s', target: 10  },
    { duration: '2m',  target: 100 },
    { duration: '5m',  target: 100 },
    { duration: '30s', target: 0   },
  ],
  thresholds: {
    'http_req_failed':   ['rate<0.01'],
    'http_req_duration': ['p(99)<2000'],
    'q3_duration_ms':    ['p(99)<5000'],
    'errors':            ['rate<0.05'],
  },
};

// ---------------------------------------------------------------------------
// Request helpers
// ---------------------------------------------------------------------------

function gqlPost(query, durationMetric, countMetric) {
  const payload = JSON.stringify({ query });
  const params = {
    headers: { 'Content-Type': 'application/json' },
    tags: { framework: FRAMEWORK },
  };
  const res = http.post(CONFIG.url, payload, params);
  const ok = check(res, {
    'HTTP 200': (r) => r.status === 200,
    'no gql errors': (r) => {
      try {
        const body = JSON.parse(r.body);
        return !body.errors || body.errors.length === 0;
      } catch { return false; }
    },
    'has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data !== null && body.data !== undefined;
      } catch { return false; }
    },
  });
  errorRate.add(!ok);
  durationMetric.add(res.timings.duration);
  countMetric.add(1);
  return res;
}

function restGet(path, durationMetric, countMetric) {
  const res = http.get(`${CONFIG.url}${path}`, {
    tags: { framework: FRAMEWORK },
  });
  const ok = check(res, { 'HTTP 200': (r) => r.status === 200 });
  errorRate.add(!ok);
  durationMetric.add(res.timings.duration);
  countMetric.add(1);
  return res;
}

function restPatch(path, body, durationMetric, countMetric) {
  const res = http.patch(`${CONFIG.url}${path}`, JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
    tags: { framework: FRAMEWORK },
  });
  const ok = check(res, { 'HTTP 200': (r) => r.status === 200 });
  errorRate.add(!ok);
  durationMetric.add(res.timings.duration);
  countMetric.add(1);
  return res;
}

// ---------------------------------------------------------------------------
// Main scenario — weighted request mix
// ---------------------------------------------------------------------------

export default function () {
  const rand = Math.random();

  if (CONFIG.type === 'graphql') {
    if (rand < 0.60) {
      group('Q1_flat', () => gqlPost(GQL_QUERIES.Q1, q1Duration, q1Requests));
    } else if (rand < 0.80) {
      group('Q2_shallow', () => gqlPost(GQL_QUERIES.Q2, q2Duration, q2Requests));
    } else if (rand < 0.95) {
      group('Q3_deep', () => gqlPost(GQL_QUERIES.Q3, q3Duration, q3Requests));
    } else {
      group('M1_mutation', () => gqlPost(GQL_QUERIES.M1, m1Duration, m1Requests));
    }
  } else {
    // REST frameworks
    if (rand < 0.60) {
      group('Q1_flat', () => restGet(REST_PATHS.Q1, q1Duration, q1Requests));
    } else if (rand < 0.80) {
      group('Q2_shallow', () => restGet(REST_PATHS.Q2, q2Duration, q2Requests));
    } else if (rand < 0.95) {
      group('Q3_deep', () => restGet(REST_PATHS.Q3, q3Duration, q3Requests));
    } else {
      group('M1_mutation', () => restPatch(
        REST_PATHS.M1,
        { bio: `bench-${Date.now()}` },
        m1Duration, m1Requests,
      ));
    }
  }

  // Minimal think time — prevents thundering herd, reflects real clients
  sleep(Math.random() * 0.1);
}

// ---------------------------------------------------------------------------
// Summary output — write structured JSON for run_all.py to aggregate
// ---------------------------------------------------------------------------

export function handleSummary(data) {
  const m = data.metrics;

  const summary = {
    framework:      FRAMEWORK,
    timestamp:      new Date().toISOString(),
    rps:            m.http_reqs?.values?.rate            ?? 0,
    p50_ms:         m.http_req_duration?.values?.['p(50)'] ?? 0,
    p95_ms:         m.http_req_duration?.values?.['p(95)'] ?? 0,
    p99_ms:         m.http_req_duration?.values?.['p(99)'] ?? 0,
    error_rate:     m.http_req_failed?.values?.rate       ?? 0,
    q1_p99_ms:      m.q1_duration_ms?.values?.['p(99)']   ?? null,
    q2_p99_ms:      m.q2_duration_ms?.values?.['p(99)']   ?? null,
    q3_p99_ms:      m.q3_duration_ms?.values?.['p(99)']   ?? null,
    q1_count:       m.q1_requests?.values?.count          ?? 0,
    q2_count:       m.q2_requests?.values?.count          ?? 0,
    q3_count:       m.q3_requests?.values?.count          ?? 0,
    m1_count:       m.m1_requests?.values?.count          ?? 0,
    total_requests: m.http_reqs?.values?.count            ?? 0,
  };

  const dateStr   = new Date().toISOString().split('T')[0];
  const outFile   = `reports/k6-${FRAMEWORK}-${dateStr}.json`;
  const stdout    = (
    `\n${'='.repeat(60)}\n` +
    `${FRAMEWORK} — k6 Benchmark Summary\n` +
    `${'='.repeat(60)}\n` +
    `RPS:      ${summary.rps.toFixed(0)}\n` +
    `p50:      ${summary.p50_ms.toFixed(1)} ms\n` +
    `p95:      ${summary.p95_ms.toFixed(1)} ms\n` +
    `p99:      ${summary.p99_ms.toFixed(1)} ms\n` +
    `Errors:   ${(summary.error_rate * 100).toFixed(2)}%\n` +
    `Requests: ${summary.total_requests}\n`
  );

  return {
    [outFile]: JSON.stringify(summary, null, 2),
    stdout,
  };
}
